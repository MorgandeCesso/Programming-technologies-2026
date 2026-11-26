from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class TextIn(StrictModel):
    @field_validator("*")
    @classmethod
    def not_blank(cls, value):
        if isinstance(value, str) and not value.strip():
            raise ValueError("поле не может быть пустым")
        return value


class SearchIn(TextIn):
    query: str
    limit: int = Field(default=3, ge=1, le=20)


class QuestionIn(TextIn):
    question: str


class MessageIn(TextIn):
    message: str


class IndexOut(BaseModel):
    documents: int
    chunks: int


class Fragment(BaseModel):
    score: float
    source: str
    chunk: int
    text: str


class SearchOut(BaseModel):
    results: list[Fragment]


class SqlOut(BaseModel):
    sql: str
    rows: list[dict[str, Any]]


class ToolCall(BaseModel):
    name: str
    arguments: dict[str, Any]
    result: str


class AnswerOut(BaseModel):
    answer: str
    tool_calls: list[ToolCall]


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorOut(BaseModel):
    error: ErrorBody
