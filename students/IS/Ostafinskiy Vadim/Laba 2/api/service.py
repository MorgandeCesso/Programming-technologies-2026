import json
from fastapi import HTTPException
from openai import APIConnectionError, APIStatusError, APITimeoutError
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session
from ai.llm_handler import llm_response
from api.schemas import Extraction
from db.models import Service, WorkshopOrder

def _error(status_code: int, code: str, detail: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "detail": detail},
    )

def parse_json_object(text: str) -> dict:
    data = json.loads(text.strip())
    if not isinstance(data, dict):
        raise ValueError("Ответ модели не является JSON-объектом")

    return data

def normalize_code(code: str | None) -> str | None:
    if code is None:
        return None
    normalized = code.strip().upper()
    return normalized or None

async def create_order(db: Session, message: str) -> WorkshopOrder:
    try:
        raw_text = await llm_response(message)
    except APITimeoutError:
        raise _error(504, "model_timeout", "Превышено время ожидания модели")
    except (APIConnectionError, APIStatusError):
        raise _error(503, "model_unavailable", "Сервер модели недоступен")
    except ValueError:
        raise _error(502, "invalid_model_response", "Модель вернула некорректный ответ")
    try:
        extracted = Extraction.model_validate(
            parse_json_object(raw_text)
        )
    except (ValueError, ValidationError):
        raise _error(502, "invalid_model_response", "Ответ модели не соответствует схеме")
    code = normalize_code(extracted.service_code)
    service = None
    if code is None:
        match_status = "not_provided"
    else:
        service = db.scalar(
            select(Service).where(Service.code == code)
        )
        if service is not None:
            match_status = "matched"
        else:
            match_status = "not_found"
    order = WorkshopOrder(
        source_text=message,
        category=extracted.category,
        summary=extracted.summary,
        service_code=code,
        item_description=extracted.item_description,
        deadline_text=extracted.deadline_text,
        details=extracted.details,
        service_id=service.id if service is not None else None,
        match_status=match_status,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

def list_orders(db: Session) -> list[WorkshopOrder]:
    return list(
        db.scalars(
            select(WorkshopOrder).order_by(WorkshopOrder.id.desc())
        )
    )

def get_order(db: Session, order_id: int) -> WorkshopOrder:
    order = db.get(WorkshopOrder, order_id)
    if order is None:
        raise _error(404, "not_found", "Заказ не найден")
    return order
