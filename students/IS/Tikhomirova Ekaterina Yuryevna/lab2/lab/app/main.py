from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from openai import APIConnectionError, APIStatusError, APITimeoutError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.database import Base, engine, get_db
from app.llm import extract_suggestion
from app.models import Course, Suggestion
from app.schemas import SuggestionCreate


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="сервис структурирования предложений",
    description=(
        "api для извлечения и сохранения предложений "
        "слушателей учебных курсов. ошибки возвращаются "
        "в формате error с полями code и message."
    ),
    version="1.0.0",
)


ERROR_CODES = {
    400: "invalid_request",
    404: "not_found",
    405: "method_not_allowed",
    422: "validation_error",
    500: "internal_error",
    502: "invalid_model_response",
    503: "model_unavailable",
    504: "model_timeout",
}


def error_response(status_code: int, message: str):
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": ERROR_CODES.get(status_code, "http_error"),
                "message": message,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request,
    error: RequestValidationError,
):
    return error_response(
        422,
        "некорректный запрос: проверь JSON, обязательные поля, "
        "типы данных и непустое содержание message",
    )


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(
    request: Request,
    error: StarletteHTTPException,
):
    if error.status_code == 404:
        message = "запись или маршрут не найдены"
    elif error.status_code == 405:
        message = "метод не поддерживается для этого маршрута"
    elif isinstance(error.detail, str):
        message = error.detail
    else:
        message = "не удалось обработать запрос"

    return error_response(error.status_code, message)


@app.exception_handler(SQLAlchemyError)
async def database_error_handler(
    request: Request,
    error: SQLAlchemyError,
):
    return error_response(
        500,
        "не удалось выполнить операцию с базой данных",
    )


@app.exception_handler(Exception)
async def unexpected_error_handler(
    request: Request,
    error: Exception,
):
    return error_response(
        500,
        "внутренняя ошибка сервиса",
    )


def serialize_suggestion(
    suggestion: Suggestion,
    course_name: str | None,
):
    return {
        "id": suggestion.id,
        "created_at": suggestion.created_at.isoformat(),
        "original_message": suggestion.original_message,
        "category": suggestion.category,
        "summary": suggestion.summary,
        "course_code": suggestion.course_code,
        "topic": suggestion.topic,
        "requested_change": suggestion.requested_change,
        "details": suggestion.details,
        "course_id": suggestion.course_id,
        "course_name": course_name,
        "match_status": suggestion.match_status,
    }


@app.post("/suggestions", status_code=201)
def create_suggestion(
    request: SuggestionCreate,
    db: Session = Depends(get_db),
):
    try:
        extracted = extract_suggestion(request.message)

    except APITimeoutError:
        raise HTTPException(
            status_code=504,
            detail="превышено время ожидания ответа языковой модели",
        ) from None

    except APIConnectionError:
        raise HTTPException(
            status_code=503,
            detail="сервер языковой модели недоступен",
        ) from None

    except APIStatusError:
        raise HTTPException(
            status_code=503,
            detail="сервер языковой модели вернул ошибку",
        ) from None

    except ValueError:
        raise HTTPException(
            status_code=502,
            detail="ответ языковой модели не соответствует заданной схеме "
            "или не является полным корректным JSON",
        ) from None

    except Exception:
        raise HTTPException(
            status_code=502,
            detail="не удалось обработать ответ языковой модели",
        ) from None

    normalized_code = (
        extracted.course_code.strip().upper()
        if extracted.course_code is not None
        else None
    )

    try:
        course = None

        if normalized_code is not None:
            course = db.query(Course).filter(
                Course.code == normalized_code
            ).first()

            match_status = "matched" if course else "not_found"
        else:
            match_status = "not_provided"

        suggestion = Suggestion(
            original_message=request.message,
            category=extracted.category,
            summary=extracted.summary,
            course_code=normalized_code,
            topic=extracted.topic,
            requested_change=extracted.requested_change,
            details=extracted.details,
            course_id=course.id if course else None,
            match_status=match_status,
        )

        course_name = course.name if course else None

        db.add(suggestion)
        db.commit()
        db.refresh(suggestion)

        return serialize_suggestion(suggestion, course_name)

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="не удалось сохранить предложение в базе данных",
        ) from None


@app.get("/suggestions")
def get_suggestions(db: Session = Depends(get_db)):
    results = db.query(
        Suggestion,
        Course.name,
    ).outerjoin(
        Course,
        Suggestion.course_id == Course.id,
    ).order_by(
        Suggestion.id,
    ).all()

    return [
        serialize_suggestion(suggestion, course_name)
        for suggestion, course_name in results
    ]


@app.get("/suggestions/{suggestion_id}")
def get_suggestion(
    suggestion_id: int,
    db: Session = Depends(get_db),
):
    result = db.query(
        Suggestion,
        Course.name,
    ).outerjoin(
        Course,
        Suggestion.course_id == Course.id,
    ).filter(
        Suggestion.id == suggestion_id,
    ).first()

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="предложение не найдено",
        )

    suggestion, course_name = result

    return serialize_suggestion(suggestion, course_name)
