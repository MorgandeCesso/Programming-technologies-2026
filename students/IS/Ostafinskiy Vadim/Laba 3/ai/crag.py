import json
from typing import Literal
from openai import AsyncOpenAI
from pydantic import BaseModel
from ai.prompt import GRADING_PROMPT
from config import BASE_URL, MODEL_NAME, MODEL_TOKEN, LLM_TIMEOUT

class ChunkGrade(BaseModel):
    number: int
    grade: Literal["подходит", "сомнительно", "не подходит"]

class GradingResult(BaseModel):
    grades: list[ChunkGrade]

async def grade_chunks(
    client: AsyncOpenAI,
    question: str,
    hits: list[dict],
) -> list[dict]:
    if not hits:
        return []
    data = {
        "question": question,
        "chunks": [
            {"number": number, **hit}
            for number, hit in enumerate(hits, start=1)
        ],
    }
    response = await client.responses.create(
        model=MODEL_NAME,
        instructions=GRADING_PROMPT,
        input=json.dumps(data, ensure_ascii=False),
        text={
            "format": {
                "type": "json_schema",
                "name": "grading",
                "schema": GradingResult.model_json_schema(),
                "strict": True,
            }
        },
        timeout=LLM_TIMEOUT,
    )
    result = GradingResult.model_validate_json(
        response.output_text
    )
    grades = {
        item.number: item.grade
        for item in result.grades
    }
    if (
        len(result.grades) != len(hits)
        or set(grades) != set(range(1, len(hits) + 1))
    ):
        raise ValueError("Некорректные оценки чанков")
    suitable = []
    for number, hit in enumerate(hits, start=1):
        grade = grades[number]
        print(
            f"CRAG: {hit['source']}, "
            f"чанк {hit['chunk']} — {grade}"
        )
        if grade != "не подходит":
            suitable.append({**hit, "grade": grade})
    return suitable
