from fastapi import APIRouter

from api.schemas import AnswerOut, MessageIn
from api.service import answer_question

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/ask", response_model=AnswerOut)
async def ask(body: MessageIn):
    return await answer_question(body.message)
