"""Тесты API с заглушкой вместо модели.

Настоящая модель не вызывается: get_llm подменяется на FakeLLM, а база - на SQLite в памяти.
Запуск: python -m pytest -v
"""
import json

import httpx
import openai
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, Event, Registration, get_db
from app.llm import LLMClient, get_llm, parse_extraction
from app.main import app

GOOD = {
    "category": "speaker",
    "summary": "Запрос на участие в качестве докладчика.",
    "event_code": "EVT-026",
    "participant_name": "Анна Смирнова",
    "participation_format": "дистанционно",
    "details": "Тема доклада - LLM в образовании.",
}


class FakeLLM:
    """Вместо модели возвращает заранее заданный текст или бросает ошибку."""

    def __init__(self, content=None, error=None):
        self.content = content
        self.error = error
        self.calls = 0

    def extract(self, message):
        self.calls += 1
        if self.error:
            raise self.error
        return parse_extraction(self.content)


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as s:
        s.add(Event(code="EVT-026", title="Конференция", event_date=None, location=None))
        s.commit()
    yield Session
    app.dependency_overrides.clear()


def make_client(Session, fake):
    def override_db():
        s = Session()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_llm] = lambda: fake
    return TestClient(app, raise_server_exceptions=False)


def count(Session, model):
    with Session() as s:
        return s.scalar(select(func.count()).select_from(model))



def test_matched(db):
    c = make_client(db, FakeLLM(json.dumps(GOOD, ensure_ascii=False)))
    r = c.post("/registrations", json={"message": "текст"})
    assert r.status_code == 201
    body = r.json()
    assert body["match_status"] == "matched"
    assert body["event_id"] == 1
    assert body["event_code"] == "EVT-026"
    assert body["id"] == 1 and body["created_at"]


def test_matched_with_case_and_spaces(db):
    data = {**GOOD, "event_code": "  evt-026 "}
    c = make_client(db, FakeLLM(json.dumps(data)))
    body = c.post("/registrations", json={"message": "текст"}).json()
    assert body["match_status"] == "matched"
    assert body["event_code"] == "evt-026"   


def test_not_found_keeps_code_and_does_not_touch_catalog(db):
    data = {**GOOD, "event_code": "EVT-999"}
    c = make_client(db, FakeLLM(json.dumps(data)))
    body = c.post("/registrations", json={"message": "текст"}).json()
    assert body["match_status"] == "not_found"
    assert body["event_id"] is None
    assert body["event_code"] == "EVT-999"
    assert count(db, Event) == 1   


def test_not_provided_and_empty_strings_become_null(db):
    data = {**GOOD, "event_code": "", "participation_format": "   "}
    c = make_client(db, FakeLLM(json.dumps(data)))
    body = c.post("/registrations", json={"message": "текст"}).json()
    assert body["match_status"] == "not_provided"
    assert body["event_code"] is None
    assert body["participation_format"] is None


def test_markdown_wrapper_is_accepted(db):
    content = "```json\n" + json.dumps(GOOD) + "\n```"
    c = make_client(db, FakeLLM(content))
    assert c.post("/registrations", json={"message": "текст"}).status_code == 201


def test_list_and_get(db):
    fake = FakeLLM(json.dumps(GOOD))
    c = make_client(db, fake)
    c.post("/registrations", json={"message": "текст"})
    assert len(c.get("/registrations").json()) == 1
    assert c.get("/registrations/1").status_code == 200
    assert fake.calls == 1   
def test_get_404(db):
    c = make_client(db, FakeLLM(json.dumps(GOOD)))
    r = c.get("/registrations/999")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"




@pytest.mark.parametrize(
    "payload",
    [{}, {"message": 123}, {"message": "   "}, {"message": None}],
    ids=["no_message", "not_string", "only_spaces", "null"],
)
def test_bad_request(db, payload):
    fake = FakeLLM(json.dumps(GOOD))
    c = make_client(db, fake)
    r = c.post("/registrations", json=payload)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "invalid_request"
    assert fake.calls == 0
    assert count(db, Registration) == 0




BAD_RESPONSES = {
    "not_json": "Конечно! Вот ответ",  # не JSON
    "empty": "",  # пустой ответ
    "not_object": json.dumps([GOOD]),  # массив вместо объекта
    "missing_key": json.dumps({k: v for k, v in GOOD.items() if k != "details"}),  # нет ключа details
    "extra_key": json.dumps({**GOOD, "extra": "x"}),  # лишний ключ
    "bad_category": json.dumps({**GOOD, "category": "guest"}),  # чужая категория
    "empty_summary": json.dumps({**GOOD, "summary": "  "}),  # пустой summary
    "list_instead_of_str": json.dumps({**GOOD, "participant_name": ["Анна"]}),  # список вместо строки
    "number_instead_of_str": json.dumps({**GOOD, "event_code": 26}),  # число вместо строки
}


@pytest.mark.parametrize("name", BAD_RESPONSES)
def test_invalid_llm_response(db, name):
    c = make_client(db, FakeLLM(BAD_RESPONSES[name]))
    r = c.post("/registrations", json={"message": "текст"})
    assert r.status_code == 502, name
    assert r.json()["error"]["code"] == "llm_invalid_response"
    assert count(db, Registration) == 0




REQ = httpx.Request("POST", "http://127.0.0.1:7000/v1/chat/completions")


def test_llm_unavailable_503(db):
    c = make_client(db, FakeLLM(error=None))
    real = LLMClient()
    real.client.chat.completions.create = lambda **kw: (_ for _ in ()).throw(
        openai.APIConnectionError(request=REQ)
    )
    app.dependency_overrides[get_llm] = lambda: real
    r = c.post("/registrations", json={"message": "текст"})
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "llm_unavailable"
    assert count(db, Registration) == 0


def test_llm_timeout_504(db):
    c = make_client(db, FakeLLM())
    real = LLMClient()
    real.client.chat.completions.create = lambda **kw: (_ for _ in ()).throw(
        openai.APITimeoutError(request=REQ)
    )
    app.dependency_overrides[get_llm] = lambda: real
    r = c.post("/registrations", json={"message": "текст"})
    assert r.status_code == 504
    assert r.json()["error"]["code"] == "llm_timeout"
    assert count(db, Registration) == 0


def test_error_has_no_traceback(db):
    c = make_client(db, FakeLLM("not json"))
    text = c.post("/registrations", json={"message": "текст"}).text
    assert "Traceback" not in text
