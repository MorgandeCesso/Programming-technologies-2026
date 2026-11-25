from typing import TypeVar

import httpx
from openai import OpenAI
from pydantic import BaseModel

from app.config import (
    LLM_MODEL,
    LLM_TIMEOUT,
    LM_API_KEY,
    LM_BASE_URL,
)


ResponseModel = TypeVar("ResponseModel", bound=BaseModel)


def generate_text(instructions: str, prompt: str) -> str:
    with httpx.Client(
        timeout=LLM_TIMEOUT,
        trust_env=False,
    ) as http_client:
        with OpenAI(
            base_url=LM_BASE_URL,
            api_key=LM_API_KEY,
            timeout=LLM_TIMEOUT,
            max_retries=0,
            http_client=http_client,
        ) as client:
            response = client.responses.create(
                model=LLM_MODEL,
                instructions=instructions,
                input=prompt,
                temperature=0,
                max_output_tokens=512,
            )

    if response.status != "completed":
        raise ValueError(
            f"генерация не завершена, статус: {response.status}"
        )

    answer = response.output_text.strip()

    if not answer:
        raise ValueError("модель вернула пустой ответ")

    return answer


def generate_structured(
    instructions: str,
    prompt: str,
    schema: type[ResponseModel],
) -> ResponseModel:
    with httpx.Client(
        timeout=LLM_TIMEOUT,
        trust_env=False,
    ) as http_client:
        with OpenAI(
            base_url=LM_BASE_URL,
            api_key=LM_API_KEY,
            timeout=LLM_TIMEOUT,
            max_retries=0,
            http_client=http_client,
        ) as client:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": instructions},
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
                max_tokens=512,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema.__name__,
                        "strict": True,
                        "schema": schema.model_json_schema(),
                    },
                },
            )

    if not response.choices:
        raise ValueError("модель не вернула результат")

    choice = response.choices[0]

    if choice.finish_reason != "stop":
        raise ValueError(
            f"генерация не завершена: {choice.finish_reason}"
        )

    if choice.message.refusal:
        raise ValueError("модель отказалась выполнять оценку")

    content = choice.message.content

    if not content or not content.strip():
        raise ValueError("модель вернула пустой ответ")

    return schema.model_validate_json(content)
