from typing import Literal
from pydantic import BaseModel, Field

class MessageIn(BaseModel):
    message: str = Field(min_length=1)
    mode: Literal["rag", "crag"] = "rag"

class AnswerOut(BaseModel):
    answer: str
