from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

Category = Literal["manufacture", "repair", "customization", "other"]

class MessageIn(BaseModel):
    message: str
    @field_validator("message")
    @classmethod
    def not_blank(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("Пустое сообщение")
        return text

class Extraction(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    category: Category
    summary: str = Field(min_length=1)
    service_code: str | None
    item_description: str | None
    deadline_text: str | None
    details: str | None
    @field_validator(
        "service_code",
        "item_description",
        "deadline_text",
        "details",
        mode="before",
    )
    @classmethod
    def empty_to_none(cls, value):
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("Ожидалась строка или null")
        text = value.strip()
        return text or None
    @field_validator("summary")
    @classmethod
    def summary_not_blank(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("Пустое краткое содержание")
        return text

class WorkshopOrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    source_text: str
    category: str
    summary: str
    service_code: str | None
    item_description: str | None
    deadline_text: str | None
    details: str | None
    service_id: int | None
    match_status: str
    