import openai
import httpx
import pytest
from docx import Document

from app import config
from app.errors import SqlError
from app.logic import chunking, text_to_sql
from app.logic.documents import parse_docx
from tests.conftest import FakeTokenizer, text_reply, tool_reply

REQ = httpx.Request("POST", "http://127.0.0.1:7000/v1/chat/completions")


def test_parse_docx_keeps_tables_and_skips_empty(tmp_path):
    document = Document()
    document.add_paragraph("Заголовок")
    document.add_paragraph("   ")
    table = document.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "L101"
    table.rows[0].cells[1].text = "Потеря линка"
    path = tmp_path / "doc.docx"
    document.save(path)
    parsed = parse_docx(path)
    assert parsed.blocks == ["Заголовок", "L101 | Потеря линка"]


def test_split_text_overlap():
    text = " ".join(f"w{i}" for i in range(1300))
    pieces = chunking.split_text(text, 600, 60, FakeTokenizer())
    assert len(pieces) == 3
    assert pieces[0].split()[0] == "w0" and pieces[0].split()[-1] == "w599"
    assert pieces[1].split()[0] == "w540"
    assert pieces[2].split()[-1] == "w1299"


def test_chunks_saved_and_loaded(tmp_path):
    chunks = [chunking.Chunk("01_Руководство", 1, "a"), chunking.Chunk("01_Руководство", 2, "b")]
    chunking.save_chunks(chunks, tmp_path)
    assert (tmp_path / "01_Руководство_1.txt").read_text(encoding="utf-8") == "a"
    assert chunking.load_chunks(tmp_path) == chunks


def test_index_and_search(client, env):
    response = client.post("/index")
    assert response.status_code == 200
    assert response.json()["documents"] == 5
    assert response.json()["chunks"] == len(list(env.temp.glob("*.txt")))
    found = client.post("/search", json={"query": "перегрев температура шасси T401", "limit": 2}).json()["results"]
    assert len(found) == 2
    assert any("T401" in item["text"] for item in found)


def test_search_before_index(client):
    response = client.post("/search", json={"query": "L101"})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "index_empty"


@pytest.mark.parametrize("payload", [{}, {"query": "  "}, {"query": 5}, {"query": "a", "limit": 0}, {"query": "a", "x": 1}])
def test_search_bad_request(client, payload):
    response = client.post("/search", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"


def test_validate_select():
    assert text_to_sql.validate_select("SELECT *\n FROM tickets;") == "SELECT * FROM tickets"
    for bad in ["DELETE FROM tickets", "SELECT 1; DROP TABLE tickets", "UPDATE tickets SET status = 'Закрыто'"]:
        with pytest.raises(SqlError):
            text_to_sql.validate_select(bad)


def test_sql_endpoint(client, use_llm):
    sql = "```sql\nSELECT number, status FROM tickets WHERE device_code = 'SW-ACC-21' AND status <> 'Закрыто'\n```"
    use_llm(text_reply(sql))
    body = client.post("/sql", json={"question": "Какие заявки по SW-ACC-21 не закрыты?"}).json()
    assert body["sql"].startswith("SELECT number, status")
    assert body["rows"] == [
        {"number": "INC-2431", "status": "Решено"},
        {"number": "INC-2438", "status": "Зарегистрировано"},
    ]


def test_sql_rejects_changes(client, use_llm, env):
    use_llm(text_reply("DELETE FROM tickets"))
    response = client.post("/sql", json={"question": "удали заявки"})
    assert response.status_code == 502
    assert response.json()["error"]["code"] == "invalid_sql"


def test_sql_unknown_column(client, use_llm):
    use_llm(text_reply("SELECT salary FROM tickets"))
    response = client.post("/sql", json={"question": "зарплаты"})
    assert response.status_code == 502
    assert response.json()["error"]["code"] == "invalid_sql"


def test_database_is_read_only(env):
    with pytest.raises(SqlError):
        from app.db.sql_store import execute_readonly

        execute_readonly("DELETE FROM tickets", 50, env.db)


def test_assistant_uses_search(client, use_llm):
    client.post("/index")
    fake = use_llm(
        tool_reply("search_knowledge_base", {"query": "код потери линка на порту"}),
        text_reply("Код L101 - потеря линка на порту."),
    )
    body = client.post("/assistant/ask", json={"message": "Какой код у потери линка на порту?"}).json()
    assert body["answer"] == "Код L101 - потеря линка на порту."
    assert body["tool_calls"][0]["name"] == "search_knowledge_base"
    tool_message = fake.requests[1]["messages"][-1]
    assert tool_message["role"] == "tool" and tool_message["tool_call_id"] == "call_1"
    assert "L101" in tool_message["content"]


def test_assistant_uses_database(client, use_llm):
    fake = use_llm(
        tool_reply("query_database", {"question": "число заявок со статусом В работе"}),
        text_reply("SELECT COUNT(*) AS total FROM tickets WHERE status = 'В работе'"),
        text_reply("В работе 2 заявки."),
    )
    body = client.post("/assistant/ask", json={"message": "Сколько заявок сейчас в работе?"}).json()
    assert body["answer"] == "В работе 2 заявки."
    assert '"total": 2' in body["tool_calls"][0]["result"]
    assert "Сколько заявок сейчас в работе?" in fake.requests[1]["messages"][1]["content"]


def test_assistant_answers_without_tools(client, use_llm):
    use_llm(text_reply("Коммутатор передаёт кадры между устройствами одной сети."))
    body = client.post("/assistant/ask", json={"message": "Что такое коммутатор?"}).json()
    assert body["tool_calls"] == []


def test_assistant_tool_error_goes_to_model(client, use_llm):
    fake = use_llm(
        tool_reply("search_knowledge_base", {"query": "L101"}),
        text_reply("База знаний пока пуста."),
    )
    body = client.post("/assistant/ask", json={"message": "Что делать при L101?"}).json()
    assert "Ошибка инструмента" in body["tool_calls"][0]["result"]
    assert fake.requests[1]["messages"][-1]["content"].startswith("Ошибка инструмента")


def test_assistant_stops_after_max_rounds(client, use_llm, monkeypatch):
    monkeypatch.setattr(config, "MAX_TOOL_ROUNDS", 2)
    client.post("/index")
    fake = use_llm(
        tool_reply("search_knowledge_base", {"query": "a"}, "c1"),
        tool_reply("search_knowledge_base", {"query": "b"}, "c2"),
        text_reply("Итог."),
    )
    body = client.post("/assistant/ask", json={"message": "вопрос"}).json()
    assert body["answer"] == "Итог."
    assert fake.requests[-1]["tools"] is None


@pytest.mark.parametrize(
    "error,status,code",
    [
        (openai.APIConnectionError(request=REQ), 503, "llm_unavailable"),
        (openai.APITimeoutError(request=REQ), 504, "llm_timeout"),
    ],
)
def test_llm_failures(client, monkeypatch, error, status, code):
    from app.logic import llm

    class Broken:
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    raise error

    monkeypatch.setattr(llm, "get_client", lambda: Broken)
    response = client.post("/assistant/ask", json={"message": "Что делать при L101?"})
    assert response.status_code == status
    assert response.json()["error"]["code"] == code


def test_empty_answer_is_502(client, use_llm):
    use_llm(text_reply("   "))
    response = client.post("/assistant/ask", json={"message": "вопрос"})
    assert response.status_code == 502
    assert response.json()["error"]["code"] == "llm_invalid_response"
