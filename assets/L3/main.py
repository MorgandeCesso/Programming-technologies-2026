import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from api.controller import router


@asynccontextmanager
async def lifespan(_: FastAPI):
    from vector_db.embedder import warmup

    await asyncio.to_thread(warmup)
    yield


app = FastAPI(
    title="Демо ЛР3: RAG-ассистент",
    description="Ответы по документам предприятия. Поиск по векторной базе модель вызывает сама.",
    lifespan=lifespan,
)
app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.exception_handler(HTTPException)
async def http_error(_, exc: HTTPException):
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        body = exc.detail
    else:
        body = {"code": "error", "detail": str(exc.detail)}
    return JSONResponse(status_code=exc.status_code, content=body)


@app.exception_handler(RequestValidationError)
async def validation_error(_, exc: RequestValidationError):
    parts = []
    for err in exc.errors():
        loc = ".".join(str(item) for item in err.get("loc", []) if item != "body")
        parts.append(f"{loc}: {err.get('msg')}" if loc else err.get("msg", ""))
    return JSONResponse(
        status_code=422,
        content={"code": "invalid_request", "detail": "; ".join(parts) or "Некорректное тело запроса"},
    )
