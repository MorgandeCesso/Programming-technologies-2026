import json
import logging

from contextlib import closing
from datetime import datetime, timezone
from openai import APIConnectionError, APIStatusError, APITimeoutError
from pydantic import ValidationError
from api.schemas import APIError, Extraction, MessageInput
from ai.prompt import SYSTEM_PROMPT, ADD_PROMPT
from ai.llm import llm_response
from json import JSONDecodeError
from db.connection import get_connection
from db.response_struct import row_to_response

logger = logging.getLogger(__name__)


def get_extraction(message: str) -> Extraction:
    input = message
    for attempt in range(2):
        try:
            content = llm_response(input)
        except APITimeoutError as exc:
            raise APIError(504, "model_timeout", "Истекло время ожидания ответа модели.") from exc
        except APIConnectionError as exc:
            raise APIError(503, "model_unavailable", "Не удалось подключиться к серверу модели.") from exc
        except APIStatusError as exc:
            logger.warning("LM Studio вернул HTTP %s для response api", exc.status_code)
            if exc.status_code == 503:
                raise APIError(
                    503,
                    "model_server_unavailable",
                    "LM Studio вернул HTTP 503. Проверьте, что модель загружена в Local Server, "
                    "сервер запущен и в LM Studio нет ошибки загрузки модели.",
                ) from exc
            raise APIError(
                502,
                "model_upstream_error",
                f"LM Studio вернул HTTP {exc.status_code} при запросе к модели.",
            ) from exc

        try:
            if not isinstance(content, str) or not content.strip():
                raise TypeError("Модель не вернула текст")
            data = json.loads(content)
            return Extraction.model_validate(data)
        except (JSONDecodeError, TypeError, ValidationError) as exc:
            if attempt == 1:
                raise APIError(
                    502,
                    "invalid_model_response",
                    "Модель дважды вернула ответ, не соответствующий требуемому JSON.",
                ) from exc


            input = (
                f"{ADD_PROMPT}{exc}\n\n"
                f"Исходное сообщение читателя:\n{message}\n\n"
                f"Твой предыдущий ответ:\n{content}"
            )

    raise APIError(502, "invalid_model_response", "Не удалось получить корректный ответ модели.")


def create_request(body: MessageInput) -> dict:
    extracted = get_extraction(body.message)
    book_code = extracted.book_code.strip() if extracted.book_code else None
    edition_id = None

    with closing(get_connection()) as connection:
        with connection:
            if book_code:
                edition = connection.execute(
                    """
                    SELECT id
                    FROM editions
                    WHERE UPPER(TRIM(book_code)) = UPPER(TRIM(?))
                    """,
                    (book_code,),
                ).fetchone()
                if edition is not None:
                    edition_id = edition["id"]

            if book_code is None:
                result_status = "not_provided"
            elif edition_id is None:
                result_status = "not_found"
            else:
                result_status = "matched"

            created_at = datetime.now(timezone.utc).isoformat()
            cursor = connection.execute(
                """
                INSERT INTO requests (
                    date, input_text, category, summary, book_code, reader_card,
                    requested_period, result_status, edition_id, details
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    created_at,
                    body.message,
                    extracted.category,
                    extracted.summary,
                    book_code,
                    extracted.reader_card,
                    extracted.requested_period,
                    result_status,
                    edition_id,
                    extracted.details,
                ),
            )
            row = connection.execute(
                "SELECT * FROM requests WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()

    return row_to_response(row)


def list_requests() -> list[dict]:
    with closing(get_connection()) as connection:
        rows = connection.execute(
            "SELECT * FROM requests ORDER BY id DESC"
        ).fetchall()
    return [row_to_response(row) for row in rows]


def get_request(request_id: int) -> dict:
    with closing(get_connection()) as connection:
        row = connection.execute(
            "SELECT * FROM requests WHERE id = ?", (request_id,)
        ).fetchone()
    if row is None:
        raise APIError(404, "request_not_found", "Запрос с таким ID не найден.")
    return row_to_response(row)