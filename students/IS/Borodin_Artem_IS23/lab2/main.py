import json
import os
import time
import importlib.util
from fastapi import FastAPI, HTTPException
from openai import APIConnectionError, APITimeoutError, OpenAI
from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv
import psycopg
import match_service

load_dotenv()

spec = importlib.util.spec_from_file_location("schema", "01_pydantic_parse.py")
schema = importlib.util.module_from_spec(spec)
spec.loader.exec_module(schema)

client = OpenAI(
    base_url=os.environ["LMSTUDIO_BASE_URL"],
    api_key=os.environ["LMSTUDIO_API_KEY"],
    timeout=60,
)

instruction = """
Верни только JSON с шестью полями:
category, summary, service_code, item_description, deadline_text, details.
category - одно из значений: manufacture, repair, customization, other.
manufacture - изготовление, repair - ремонт, customization - гравировка или персонализация.
Если категория неясна, поставь other.
summary - краткое содержание, непустая строка.
service_code - код услуги из текста или null. Не выдумывай код и не подбирай его по названию.
item_description - изделие или null.
deadline_text - срок так, как он написан, или null. Даты не пересчитывай.
details - важная деталь, которой нет в остальных полях, или null.
Не придумывай отсутствующие сведения. Не пиши SQL. Других полей не добавляй.
"""

app = FastAPI(title="Приём заказов мастерской")


class MessageIn(BaseModel):
    message: str


def error(status_code, code, description):
    raise HTTPException(
        status_code=status_code,
        detail={"error": code, "description": description},
    )


def ask_model(message):
    try:
        start = time.perf_counter()
        response = client.chat.completions.create(
            model=os.environ["LMSTUDIO_MODEL"],
            temperature=0,
            messages=[
                {"role": "system", "content": instruction},
                {"role": "user", "content": message},
            ],
        )
        seconds = time.perf_counter() - start
    except APITimeoutError:
        error(504, "model_timeout", "Модель не ответила за 60 секунд")
    except APIConnectionError:
        error(503, "model_unavailable", "Сервер модели недоступен")

    usage = response.usage
    print(f"Входные токены: {usage.prompt_tokens}")
    print(f"Токены ответа: {usage.completion_tokens}")
    print(f"Всего токенов: {usage.total_tokens}")
    print(f"Время: {seconds:.1f} с")
    print(f"Токенов в секунду: {usage.completion_tokens / seconds:.1f}")

    text = response.choices[0].message.content.strip()
    if text.startswith("```"):
        lines = text.splitlines()[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)

    try:
        return schema.check_order(json.loads(text))
    except (json.JSONDecodeError, ValueError, ValidationError):
        error(502, "invalid_model_response", "Ответ модели не прошёл проверку")


def row_to_order(row):
    return {
        "id": row[0],
        "created_at": row[1],
        "message": row[2],
        "category": row[3],
        "summary": row[4],
        "service_code": row[5],
        "item_description": row[6],
        "deadline_text": row[7],
        "details": row[8],
        "service_id": row[9],
        "match_status": row[10],
    }


def save_order(message, order, service_id, status, saved_code):
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO orders (
                    message, category, summary, service_code,
                    item_description, deadline_text, details,
                    service_id, match_status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, created_at, message, category, summary,
                          service_code, item_description, deadline_text,
                          details, service_id, match_status
                """,
                (
                    message,
                    order.category,
                    order.summary,
                    saved_code,
                    order.item_description,
                    order.deadline_text,
                    order.details,
                    service_id,
                    status,
                ),
            )
            row = cur.fetchone()
        conn.commit()
    return row_to_order(row)


@app.post("/workshop-orders", status_code=201)
def create_order(body: MessageIn):
    message = body.message.strip()
    if message == "":
        error(400, "empty_message", "Сообщение пустое")

    order = ask_model(message)
    service_id, status, saved_code = match_service.match_service(order.service_code)
    return save_order(message, order, service_id, status, saved_code)


@app.get("/workshop-orders")
def list_orders():
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, created_at, message, category, summary,
                       service_code, item_description, deadline_text,
                       details, service_id, match_status
                FROM orders
                ORDER BY id
                """
            )
            rows = cur.fetchall()
    return [row_to_order(row) for row in rows]


@app.get("/workshop-orders/{order_id}")
def get_order(order_id: int):
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, created_at, message, category, summary,
                       service_code, item_description, deadline_text,
                       details, service_id, match_status
                FROM orders
                WHERE id = %s
                """,
                (order_id,),
            )
            row = cur.fetchone()
    if row is None:
        error(404, "order_not_found", "Заказ не найден")
    return row_to_order(row)