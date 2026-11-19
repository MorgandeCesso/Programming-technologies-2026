from pydantic import BaseModel, ConfigDict, StrictStr, ValidationError, field_validator
from typing import Literal

class APIError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message


class MessageInput(BaseModel):
    message: StrictStr

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message не должно быть пустым")
        return value.strip()


class Extraction(BaseModel):
    category: Literal["borrow", "renew", "availability", "other"]
    summary: StrictStr
    book_code: StrictStr | None
    reader_card: StrictStr | None
    requested_period: StrictStr | None
    details: StrictStr | None

    model_config = ConfigDict(extra="forbid")

    @field_validator("summary")
    @classmethod
    def summary_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("summary не должно быть пустым")
        return value.strip()

    @field_validator("book_code", "reader_card", "requested_period", "details", mode="before")
    @classmethod
    def blank_optional_strings_become_null(cls, value):
        if isinstance(value, str) and not value.strip():
            return None
        return value