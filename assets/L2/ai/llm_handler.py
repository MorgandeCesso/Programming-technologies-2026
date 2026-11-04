from openai import AsyncOpenAI

from ai.prompt import SYSTEM_PROMPT
from config import BASE_URL, LLM_TIMEOUT, MODEL, MODEL_TOKEN

client = AsyncOpenAI(
    base_url=BASE_URL,
    api_key=MODEL_TOKEN or "not-set",
    timeout=LLM_TIMEOUT,
)


async def llm_response(message: str) -> str:
    response = await client.responses.create(
        model=MODEL,
        instructions=SYSTEM_PROMPT,
        input=message,
        timeout=LLM_TIMEOUT,
    )
    return response.output_text
