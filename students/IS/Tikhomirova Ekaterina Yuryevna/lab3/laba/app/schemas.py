from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AskRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
    )

    message: str = Field(min_length=1, max_length=4000)
    mode: Literal["rag", "crag"] = "rag"
    limit: int = Field(default=3, ge=1, le=20)

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("сообщение не должно быть пустым")

        return value


class SourceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    source: str
    chunk: int
    score: float
    text: str

    grade: Literal[
        "relevant",
        "partial",
        "irrelevant",
        "invalid",
    ] | None = None

    reason: str | None = None
    evidence: str | None = None
    used: bool | None = None


class AskResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["rag", "crag"]
    answer: str = Field(min_length=1)
    sources: list[SourceResponse]