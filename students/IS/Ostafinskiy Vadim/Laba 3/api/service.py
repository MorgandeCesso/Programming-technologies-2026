from fastapi import HTTPException
from openai import APITimeoutError, APIConnectionError, APIStatusError
from ai.llm_handler import llm_response
from api.schemas import AnswerOut

async def answer_question (message: str, mode: str) -> AnswerOut:
    try:
        text = await llm_response(message, mode)
    except APITimeoutError as exc:
        raise HTTPException(
            status_code=504,
            detail="Превышено время ожидания ответа модели",
        ) from exc
    except (APIConnectionError, APIStatusError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Модель недоступна",
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail="Некорректный вызов инструмента",
        ) from exc
    if not text or not text.strip():
        raise HTTPException(
            status_code=502,
            detail="Модель вернула пустой ответ",
        )
    return AnswerOut(answer=text)
