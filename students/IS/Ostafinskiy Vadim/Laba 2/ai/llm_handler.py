
from openai import AsyncOpenAI

from ai.prompt import SYSTEM_PROMPT
from api.schemas import Extraction
from config import MODEL, BASE_URL, API_KEY, LLM_TIMEOUT


client = AsyncOpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
    timeout=LLM_TIMEOUT,
    max_retries=0,
)


async def llm_response(message: str) -> str:
    response = await client.responses.create(
        model=MODEL,
        instructions=SYSTEM_PROMPT,
        input=message,
        text={
            "format": {
                "type": "json_schema",
                "name": "workshop_order",
                "strict": True,
                "schema": Extraction.model_json_schema(),
            }
        },
        store=False,
    )

    if response.status != "completed":
        raise ValueError("Ответ модели не завершён")

    for item in response.output:
        if item.type == "message":
            for part in item.content:
                if part.type == "refusal":
                    raise ValueError("Модель отказалась формировать ответ")

    if not response.output_text.strip():
        raise ValueError("Модель вернула пустой ответ")

    return response.output_text
