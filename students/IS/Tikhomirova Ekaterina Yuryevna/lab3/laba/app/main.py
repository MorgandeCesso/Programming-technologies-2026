import logging

import httpx
from fastapi import FastAPI, HTTPException
from openai import APIConnectionError, APIStatusError, APITimeoutError

from app.logic.assistant import ask
from app.schemas import AskRequest, AskResponse


logger = logging.getLogger(__name__)

app = FastAPI(
    title="помощник по документации телеметрии",
    description="классический RAG и CRAG с локальными моделями",
    version="1.0.0",
)


@app.post(
    "/assistant/ask",
    response_model=AskResponse,
    response_model_exclude_unset=True,
)
def ask_assistant(request: AskRequest) -> AskResponse:
    try:
        result = ask(
            message=request.message,
            mode=request.mode,
            limit=request.limit,
        )

        return AskResponse.model_validate(result)

    except (APITimeoutError, httpx.TimeoutException) as error:
        raise HTTPException(
            status_code=504,
            detail={
                "code": "model_timeout",
                "message": "превышено время ожидания модели",
            },
        ) from error

    except (APIConnectionError, httpx.RequestError) as error:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "model_unavailable",
                "message": "не удалось подключиться к серверу моделей",
            },
        ) from error

    except (APIStatusError, httpx.HTTPStatusError) as error:
        raise HTTPException(
            status_code=502,
            detail={
                "code": "model_service_error",
                "message": "сервер моделей вернул ошибку",
            },
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=502,
            detail={
                "code": "processing_error",
                "message": (
                    "не удалось обработать запрос: проверьте "
                    "индексацию базы и ответы модели"
                ),
            },
        ) from error

    except Exception as error:
        logger.error(
            "непредвиденная ошибка обработки: %s",
            type(error).__name__,
        )

        raise HTTPException(
            status_code=500,
            detail={
                "code": "internal_error",
                "message": "внутренняя ошибка приложения",
            },
        ) from error