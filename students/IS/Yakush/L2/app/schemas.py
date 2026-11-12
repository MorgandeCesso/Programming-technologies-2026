"""Pydantic-схемы: проверка ответа модели, тело запроса и ответы API."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

Category = Literal["attendee", "speaker", "volunteer", "other"]
MatchStatus = Literal["matched", "not_found", "not_provided"]


class Extraction(BaseModel):
    """Ровно шесть полей, которые должна вернуть модель.

    extra="forbid"  - лишние ключи запрещены;
    strict=True     - типы не подгоняются (число или список не превратится в строку);
    поля без значения по умолчанию - значит все ключи обязательны.
    """
    model_config = ConfigDict(extra="forbid", strict=True)

    category: Category
    summary: str
    event_code: str | None
    participant_name: str | None
    participation_format: str | None
    details: str | None

    @field_validator("summary")
    @classmethod
    def summary_not_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("summary не может быть пустым")
        return value

    @field_validator("event_code", "participant_name", "participation_format", "details")
    @classmethod
    def empty_to_null(cls, value: str | None) -> str | None:
        """Правило: пустая строка или одни пробелы в необязательном поле -> null."""
        if value is None:
            return None
        value = value.strip()
        return value or None


class MessageIn(BaseModel):
    """Тело запроса POST /registrations."""
    model_config = ConfigDict(extra="forbid", strict=True)

    message: str

    @field_validator("message")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message не может быть пустым")
        return value


class RegistrationOut(BaseModel):
    """Запись в ответе API. Служебные поля формирует приложение, а не модель."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    message: str
    category: Category
    summary: str
    event_code: str | None
    participant_name: str | None
    participation_format: str | None
    details: str | None
    event_id: int | None
    match_status: MatchStatus


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorOut(BaseModel):
    """Единый формат ошибки: {"error": {"code": ..., "message": ...}}"""
    error: ErrorBody
