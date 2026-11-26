import asyncio
import json
from openai import AsyncOpenAI
from ai.prompt import SYSTEM_PROMPT
from config import BASE_URL, LLM_TIMEOUT, MODEL_NAME, MODEL_TOKEN
from ai.crag import grade_chunks

client = AsyncOpenAI(
    base_url=BASE_URL,
    api_key=MODEL_TOKEN or "not-set",
    timeout=LLM_TIMEOUT,
    max_retries=0,
)

MAX_TOOL_ROUNDS = 3

TOOLS = [
    {
        "type": "function",
        "name": "search_knowledge_base",
        "description": "Поиск информации в документах мастерской",
        "strict": False,
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Короткий поисковый запрос по документам мастерской",
                }
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    }
]

async def llm_response(message: str, mode: str = "rag") -> str:
    if not BASE_URL or not MODEL_NAME:
        raise RuntimeError("Не настроено подключение к модели")
    conversation = [
        {"role": "user", "content": message}
    ]
    response = await client.responses.create(
        model=MODEL_NAME,
        instructions=SYSTEM_PROMPT,
        input=conversation,
        tools=TOOLS,
        tool_choice="auto",
        timeout=LLM_TIMEOUT,
    )
    for _ in range(MAX_TOOL_ROUNDS):
        calls = [
            item for item in response.output
            if item.type == "function_call"
        ]
        if not calls:
            return response.output_text
        conversation.extend(response.output)
        for call in calls:
            conversation.append(
                {
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": await _call_tool
                    (
                        call.name, call.arguments, message, mode
                    ),
                }
            )
        response = await client.responses.create(
            model=MODEL_NAME,
            instructions=SYSTEM_PROMPT,
            input=conversation,
            tools=TOOLS,
            tool_choice="auto",
            timeout=LLM_TIMEOUT,
        )
    return response.output_text

async def _call_tool(
    name: str,
    arguments,
    message: str,
    mode: str,
    ) -> str:
    if name != "search_knowledge_base":
        return json.dumps(
            {"error": "Неизвестный инструмент"},
            ensure_ascii=False,
        )
    payload = _parse_arguments(arguments)
    query = str(payload.get("query", "")).strip()
    if not query:
        return json.dumps(
            {"error": "Пустой запрос"},
            ensure_ascii=False,
        )
    hits = await asyncio.to_thread(_search, query)
    if mode == "crag":
        hits = await grade_chunks(client, message, hits)
        if not any(
            hit["grade"] == "подходит" for hit in hits
        ):
            return json.dumps(
                {
                    "message": "В документах нет достаточной "
                               "информации для ответа"
                },
                ensure_ascii=False,
            )
    return json.dumps(hits, ensure_ascii=False)

def _search(query: str) -> list[dict]:
    from vector_db.embedder import search
    return [
        {
            "source": hit["source"],
            "chunk": hit["chunk"],
            "text": hit["text"],
        }
        for hit in search(query, limit=3)
    ]

def _parse_arguments(arguments) -> dict:
    if isinstance(arguments, dict):
        return arguments
    if not arguments:
        return {}
    data = json.loads(arguments)
    if not isinstance(data, dict):
        raise ValueError("Некорректные аргументы инструмента")
    return data
