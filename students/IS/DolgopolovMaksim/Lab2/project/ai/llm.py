from openai import OpenAI
from ai.prompt import SYSTEM_PROMPT
from config import BASE_URL, LLM_TIMEOUT, MODEL_NAME, API_KEY, TEMPERATURE

client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
    timeout=LLM_TIMEOUT,
    max_retries=2,
)

def llm_response(message: str) -> str | None:
    response = client.responses.create(
        model=MODEL_NAME,
        input=message,
        temperature=TEMPERATURE,
        instructions=SYSTEM_PROMPT,
    )
    return response.output_text