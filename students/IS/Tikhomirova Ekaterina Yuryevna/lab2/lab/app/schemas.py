from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SuggestionExtracted(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        str_strip_whitespace=True,
    )

    category: Literal["content", "practice", "schedule", "other"]
    summary: str = Field(min_length=1)
    course_code: str | None
    topic: str | None
    requested_change: str | None
    details: str | None

    @field_validator(
        "course_code",
        "topic",
        "requested_change",
        "details",
        mode="before",
    )
    @classmethod
    def empty_string_to_none(cls, value):
        if isinstance(value, str) and not value.strip():
            return None
        return value


class SuggestionCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
    )

    message: str = Field(min_length=1)

    @field_validator("message")
    @classmethod
    def validate_message(cls, value):
        if not value.strip():
            raise ValueError("сообщение не должно быть пустым")
        return value
    