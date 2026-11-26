import json

from app import config
from app.errors import AppError, LLMInvalidResponse
from app.logic import indexing, llm, text_to_sql

SYSTEM_PROMPT = """
Ты ассистент отдела эксплуатации сетевой инфраструктуры ООО «Северный контур». Отвечай на русском, коротко и по делу.

У тебя есть два инструмента:
- search_knowledge_base - поиск по документам отдела: руководство с кодами аварий и действиями инженера, регламент обработки инцидентов (приоритеты, сроки, статусы, эскалация, внутренние номера), реестр оборудования (расположение, IP-адреса, ответственные, ЗИП), инструкция по мониторингу (метрики и пороги), журнал выполненных работ.
- query_database - запрос к базе мониторинга с таблицами событий, заявок и устройств. Используй его, когда нужно посчитать, отобрать или перечислить события и заявки по устройствам, датам, статусам, приоритетам и причинам отказа.

Если для ответа нужны данные предприятия, вызови подходящий инструмент. Если вопрос общий и данные предприятия не нужны, отвечай сразу.
Коды аварий, номера заявок, сроки, адреса, имена и числа бери только из результатов инструментов. Ничего не придумывай.
Если в результатах нет нужных данных, прямо скажи, что в документах или в базе этого нет.
""".strip()

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Найти фрагменты документов отдела, относящиеся к вопросу",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Короткий поисковый запрос"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_database",
            "description": "Получить данные из базы мониторинга: события, заявки, устройства",
            "parameters": {
                "type": "object",
                "properties": {"question": {"type": "string", "description": "Что нужно найти или посчитать"}},
                "required": ["question"],
            },
        },
    },
]


def run_tool(name: str, arguments: dict, user_message: str) -> str:
    try:
        if name == "search_knowledge_base":
            found = indexing.search(str(arguments.get("query", user_message)))
            return json.dumps(
                [{"source": item["source"], "chunk": item["chunk"], "text": item["text"]} for item in found],
                ensure_ascii=False,
            )
        if name == "query_database":
            result = text_to_sql.ask_database(str(arguments.get("question", user_message)), user_message)
            return json.dumps(result, ensure_ascii=False, default=str)
    except AppError as error:
        return f"Ошибка инструмента: {error.message}"
    return f"Неизвестный инструмент {name}"


def _parse_arguments(raw: str | None) -> dict:
    try:
        value = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def ask(message: str) -> dict:
    conversation = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": message},
    ]
    calls = []
    for _ in range(config.MAX_TOOL_ROUNDS):
        reply = llm.chat(conversation, TOOLS)
        if not reply.tool_calls:
            answer = (reply.content or "").strip()
            if not answer:
                raise LLMInvalidResponse("Модель вернула пустой ответ")
            return {"answer": answer, "tool_calls": calls}
        conversation.append(
            {
                "role": "assistant",
                "content": reply.content or "",
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {"name": call.function.name, "arguments": call.function.arguments},
                    }
                    for call in reply.tool_calls
                ],
            }
        )
        for call in reply.tool_calls:
            arguments = _parse_arguments(call.function.arguments)
            result = run_tool(call.function.name, arguments, message)
            calls.append({"name": call.function.name, "arguments": arguments, "result": result})
            conversation.append({"role": "tool", "tool_call_id": call.id, "content": result})
    reply = llm.chat(conversation)
    answer = (reply.content or "").strip()
    if not answer:
        raise LLMInvalidResponse("Модель не сформулировала ответ")
    return {"answer": answer, "tool_calls": calls}
