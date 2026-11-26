import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.schemas import AnswerOut, ErrorOut, IndexOut, MessageIn, QuestionIn, SearchIn, SearchOut, SqlOut
from app.errors import AppError
from app.logic import assistant, indexing, text_to_sql

logger = logging.getLogger(__name__)

app = FastAPI(title="RAG-ассистент отдела эксплуатации сети")

ERRORS = {code: {"model": ErrorOut} for code in (409, 422, 502, 503, 504)}


def error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


@app.exception_handler(RequestValidationError)
def validation_handler(request: Request, exc: RequestValidationError):
    fields = sorted({".".join(str(part) for part in item["loc"][1:]) or "body" for item in exc.errors()})
    return error(422, "invalid_request", "Неверное тело запроса: " + ", ".join(fields))


@app.exception_handler(AppError)
def app_error_handler(request: Request, exc: AppError):
    return error(exc.status, exc.code, exc.message)


@app.exception_handler(Exception)
def unexpected_handler(request: Request, exc: Exception):
    logger.exception("Необработанная ошибка")
    return error(500, "internal_error", "Внутренняя ошибка сервиса")


@app.post("/index", response_model=IndexOut, responses=ERRORS)
def index():
    return indexing.index_documents()


@app.post("/search", response_model=SearchOut, responses=ERRORS)
def search(body: SearchIn):
    return {"results": indexing.search(body.query, body.limit)}


@app.post("/sql", response_model=SqlOut, responses=ERRORS)
def sql(body: QuestionIn):
    return text_to_sql.ask_database(body.question)


@app.post("/assistant/ask", response_model=AnswerOut, responses=ERRORS)
def ask(body: MessageIn):
    return assistant.ask(body.message)
