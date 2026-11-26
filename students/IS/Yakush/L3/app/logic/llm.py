from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI

from app import config
from app.errors import LLMError, LLMInvalidResponse, LLMTimeout, LLMUnavailable

_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            base_url=config.LLM_BASE_URL,
            api_key=config.LLM_API_KEY or "lm-studio",
            timeout=config.LLM_TIMEOUT,
            max_retries=0,
        )
    return _client


def chat(messages: list[dict], tools: list[dict] | None = None):
    kwargs = {
        "model": config.LLM_MODEL,
        "messages": messages,
        "temperature": config.LLM_TEMPERATURE,
        "max_tokens": config.LLM_MAX_TOKENS,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    try:
        response = get_client().chat.completions.create(**kwargs)
    except APITimeoutError:
        raise LLMTimeout("Модель не ответила за отведённое время")
    except APIConnectionError:
        raise LLMUnavailable("Сервер модели недоступен")
    except APIStatusError as error:
        raise LLMError(f"Сервер модели вернул ошибку {error.status_code}")
    if not response.choices:
        raise LLMInvalidResponse("Модель вернула пустой ответ")
    choice = response.choices[0]
    if choice.finish_reason == "length":
        raise LLMInvalidResponse("Ответ модели обрезан по max_tokens")
    return choice.message


def strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    return text.strip()
