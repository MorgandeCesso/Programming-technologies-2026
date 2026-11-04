import json

from fastapi import HTTPException
from openai import APIConnectionError, APIStatusError, APITimeoutError
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from ai.llm_handler import llm_response
from api.schemas import Extraction
from db.models import Enclosure, Note


def _error(status_code: int, code: str, detail: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "detail": detail})


def parse_json_object(text: str) -> dict:
    candidate = text.strip()
    if candidate.startswith("```"):
        candidate = candidate.strip("`")
        candidate = candidate.removeprefix("json").strip()
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError:
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start == -1 or end <= start:
            raise ValueError("json not found")
        data = json.loads(candidate[start : end + 1])
    if not isinstance(data, dict):
        raise ValueError("json is not an object")
    return data


def normalize_code(code: str | None) -> str | None:
    if code is None:
        return None
    normalized = code.strip().upper()
    return normalized or None


async def create_note(db: Session, message: str) -> Note:
    try:
        raw_text = await llm_response(message)
    except APITimeoutError:
        raise _error(504, "model_timeout", "Превышено время ожидания модели")
    except (APIConnectionError, APIStatusError):
        raise _error(503, "model_unavailable", "Сервер модели недоступен")

    try:
        extracted = Extraction.model_validate(parse_json_object(raw_text))
    except (ValueError, json.JSONDecodeError, ValidationError):
        raise _error(502, "invalid_model_response", "Ответ модели не соответствует схеме")

    code = normalize_code(extracted.enclosure_code)
    enclosure = None
    if code is None:
        match_status = "not_provided"
    else:
        enclosure = db.scalar(select(Enclosure).where(Enclosure.code == code))
        match_status = "matched" if enclosure is not None else "not_found"

    note = Note(
        source_text=message,
        category=extracted.category,
        summary=extracted.summary,
        enclosure_code=code,
        animal_text=extracted.animal_text,
        observation_text=extracted.observation_text,
        details=extracted.details,
        enclosure_id=enclosure.id if enclosure is not None else None,
        match_status=match_status,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def list_notes(db: Session) -> list[Note]:
    return list(db.scalars(select(Note).order_by(Note.id.desc())))


def get_note(db: Session, note_id: int) -> Note:
    note = db.get(Note, note_id)
    if note is None:
        raise _error(404, "not_found", "Запись не найдена")
    return note
