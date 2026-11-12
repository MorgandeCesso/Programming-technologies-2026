"""Работа с локальной моделью: инструкция, вызов, разбор и проверка ответа."""
import json

import openai
from openai import OpenAI
from pydantic import ValidationError

from app import config
from app.schemas import Extraction

SYSTEM_PROMPT = """Ты извлекаешь сведения из сообщений о предполагаемом участии в мероприятиях.
Сообщение пользователя придёт отдельно. Верни ТОЛЬКО один JSON-объект, без пояснений и без markdown.

В объекте ровно шесть ключей, все обязательны:
- "category": одна из категорий:
    "attendee"  - участие как слушатель или посетитель;
    "speaker"   - участие как докладчик, выступление с докладом;
    "volunteer" - участие как волонтёр, помощь в проведении;
    "other"     - всё остальное или если категория неоднозначна (например, вопрос о мероприятии).
- "summary": краткое содержание сообщения одним предложением на русском, непустая строка.
- "event_code": код мероприятия ровно так, как он написан в сообщении (например "EVT-026"), иначе null.
- "participant_name": имя участника, если оно указано в сообщении, иначе null.
- "participation_format": формат участия, только если он явно указан (например "очно", "дистанционно", "онлайн"), иначе null.
- "details": другие существенные сведения из сообщения, которые не вошли в остальные поля (например тема доклада), иначе null.

Правила:
- Ничего не придумывай. Если сведений нет в сообщении, ставь null.
- Если указано только название мероприятия без кода, event_code = null, а название можно упомянуть в summary или details.
- Значения полей - строки или null. Числа и даты пиши как текст из сообщения.

Пример. Сообщение: "Я Анна Смирнова, хочу выступить на EVT-026 дистанционно с докладом о применении LLM в образовании."
Ответ:
{"category": "speaker", "summary": "Запрос на участие в мероприятии в качестве докладчика.", "event_code": "EVT-026", "participant_name": "Анна Смирнова", "participation_format": "дистанционно", "details": "Тема доклада - применение LLM в образовании."}"""


class LLMError(Exception):
    """Базовая ошибка работы с моделью. status и code уходят в HTTP-ответ."""
    status = 502
    code = "llm_error"


class LLMUnavailable(LLMError):
    status = 503
    code = "llm_unavailable"


class LLMTimeout(LLMError):
    status = 504
    code = "llm_timeout"


class LLMInvalidResponse(LLMError):
    status = 502
    code = "llm_invalid_response"


def parse_extraction(content: str | None) -> Extraction:
    """Разбирает текст ответа модели и проверяет его по схеме Extraction."""
    if not content or not content.strip():
        raise LLMInvalidResponse("Модель вернула пустой ответ")

    text = content.strip()
    
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        raise LLMInvalidResponse("Ответ модели не является валидным JSON")

    if not isinstance(data, dict):
        raise LLMInvalidResponse("Ответ модели должен быть JSON-объектом")

    try:
        return Extraction.model_validate(data)
    except ValidationError as e:
       
        fields = sorted({".".join(str(p) for p in err["loc"]) or "?" for err in e.errors()})
        raise LLMInvalidResponse("Ответ модели нарушает схему, поля: " + ", ".join(fields))


class LLMClient:
    """Клиент локальной модели. Параметры подключения берутся из config."""

    def __init__(self) -> None:
        self.client = OpenAI(
            base_url=config.LLM_BASE_URL,
            api_key=config.LLM_API_KEY or "not-set",
            timeout=config.LLM_TIMEOUT,   # конечный тайм-аут
            max_retries=0,                # без повторных попыток
        )

    def extract(self, message: str) -> Extraction:
        try:
            response = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": message},   # сообщение передаётся отдельно
                ],
                temperature=config.LLM_TEMPERATURE,
                max_tokens=config.LLM_MAX_TOKENS,
            )
       
        except openai.APITimeoutError:
            raise LLMTimeout("Превышено время ожидания ответа модели")
        except openai.APIConnectionError:
            raise LLMUnavailable("Сервер модели недоступен")
        except openai.APIStatusError as e:
            raise LLMError(f"Сервер модели вернул ошибку {e.status_code}")

        choice = response.choices[0]
        if choice.finish_reason == "length":
            raise LLMInvalidResponse("Ответ модели оборван по лимиту токенов")
        return parse_extraction(choice.message.content)


def get_llm() -> LLMClient:
    """Зависимость FastAPI. В тестах подменяется заглушкой."""
    return LLMClient()
