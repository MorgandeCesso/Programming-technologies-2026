import json

from fastapi import HTTPException
from openai import APIConnectionError, APIStatusError, APITimeoutError

from ai.llm_handler import llm_response
from api.schemas import AnswerOut


def _error(status_code: int, code: str, detail: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "detail": detail})


async def answer_question(message: str) -> AnswerOut:
    try:
        answer = await llm_response(message)
    except APITimeoutError:
        raise _error(504, "model_timeout", "Превышено время ожидания модели")
    except (APIConnectionError, APIStatusError):
        raise _error(503, "model_unavailable", "Сервер модели недоступен")
    except RuntimeError as exc:
        raise _error(500, "config_error", str(exc))
    except (ValueError, json.JSONDecodeError):
        raise _error(502, "invalid_tool_call", "Модель передала некорректные аргументы функции")

    text = answer.strip()
    if not text:
        raise _error(502, "empty_model_response", "Модель вернула пустой ответ")
    return AnswerOut(answer=text)
