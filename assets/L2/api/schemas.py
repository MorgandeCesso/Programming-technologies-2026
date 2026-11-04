from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Category = Literal["feeding", "health", "habitat", "other"]


class MessageIn(BaseModel):
    message: str

    @field_validator("message")
    @classmethod
    def not_blank(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("пустое сообщение")
        return text


class Extraction(BaseModel):
    """Схема ответа модели."""

    model_config = ConfigDict(extra="forbid", strict=True)

    category: Category
    summary: str = Field(min_length=1)
    enclosure_code: str | None
    animal_text: str | None
    observation_text: str | None
    details: str | None

    @field_validator(
        "enclosure_code",
        "animal_text",
        "observation_text",
        "details",
        mode="before",
    )
    @classmethod
    def empty_to_none(cls, value):
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("ожидалась строка или null")
        text = value.strip()
        return text or None

    @field_validator("summary")
    @classmethod
    def summary_not_blank(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("пустое краткое содержание")
        return text


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    source_text: str
    category: str
    summary: str
    enclosure_code: str | None
    animal_text: str | None
    observation_text: str | None
    details: str | None
    enclosure_id: int | None
    match_status: str
