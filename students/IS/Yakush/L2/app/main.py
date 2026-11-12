"""FastAPI-приложение: эндпоинты /registrations и обработка ошибок."""
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import Event, Registration, get_db, init_db, normalize_code
from app.llm import LLMClient, LLMError, get_llm
from app.schemas import ErrorOut, MessageIn, RegistrationOut


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()   # создать таблицы при запуске, если их нет
    yield


app = FastAPI(
    title="Регистрация на мероприятия",
    description="ЛР2, вариант 4: извлечение намерения участия из текста с помощью локальной LLM",
    lifespan=lifespan,
)


def error(status: int, code: str, message: str) -> JSONResponse:
    """Единый формат ошибок."""
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


class NotFound(Exception):
    pass


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
  
    fields = sorted({".".join(str(p) for p in e["loc"][1:]) or "body" for e in exc.errors()})
    return error(422, "invalid_request", "Неверное тело запроса, поля: " + ", ".join(fields))


@app.exception_handler(LLMError)
async def llm_handler(request: Request, exc: LLMError):
    return error(exc.status, exc.code, str(exc))


@app.exception_handler(NotFound)
async def not_found_handler(request: Request, exc: NotFound):
    return error(404, "not_found", str(exc))


@app.exception_handler(Exception)
async def unexpected_handler(request: Request, exc: Exception):
    return error(500, "internal_error", "Внутренняя ошибка сервиса")


ERRORS = {
    404: {"model": ErrorOut, "description": "Запись не найдена"},
    422: {"model": ErrorOut, "description": "Неверное тело запроса"},
    502: {"model": ErrorOut, "description": "Ответ модели не JSON или нарушает схему"},
    503: {"model": ErrorOut, "description": "Сервер модели недоступен"},
    504: {"model": ErrorOut, "description": "Превышен тайм-аут ожидания модели"},
}


@app.post(
    "/registrations",
    status_code=201,
    response_model=RegistrationOut,
    responses={k: ERRORS[k] for k in (422, 502, 503, 504)},
    summary="Принять сообщение, извлечь сведения моделью и сохранить",
)
def create_registration(
    body: MessageIn,
    db: Session = Depends(get_db),
    llm: LLMClient = Depends(get_llm),
):
    # 1. Модель извлекает и проверяет поля. При ошибке исключение -> 502/503/504, ничего не сохраняется
    extracted = llm.extract(body.message)

    # 2. Сопоставление кода со справочником (справочник только читаем)
    event_id = None
    if extracted.event_code is None:
        match_status = "not_provided"
    else:
        event = db.scalar(select(Event).where(Event.code == normalize_code(extracted.event_code)))
        if event:
            event_id, match_status = event.id, "matched"
        else:
            match_status = "not_found"

    # 3. Сохранение
    record = Registration(
        message=body.message,
        **extracted.model_dump(),
        event_id=event_id,
        match_status=match_status,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@app.get("/registrations", response_model=list[RegistrationOut], summary="Список сохранённых записей")
def list_registrations(db: Session = Depends(get_db)):
    return db.scalars(select(Registration).order_by(Registration.id)).all()


@app.get(
    "/registrations/{registration_id}",
    response_model=RegistrationOut,
    responses={404: ERRORS[404]},
    summary="Одна запись по ID",
)
def get_registration(registration_id: int, db: Session = Depends(get_db)):
    record = db.get(Registration, registration_id)
    if record is None:
        raise NotFound(f"Запись с id={registration_id} не найдена")
    return record
