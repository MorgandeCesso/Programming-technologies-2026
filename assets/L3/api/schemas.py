from pydantic import BaseModel, Field, field_validator


class MessageIn(BaseModel):
    message: str = Field(min_length=1)

    @field_validator("message")
    @classmethod
    def not_blank(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("пустое сообщение")
        return text


class AnswerOut(BaseModel):
    answer: str
