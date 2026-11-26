import math

import httpx

from app.config import (
    EMBEDDING_MODEL,
    LLM_TIMEOUT,
    LM_API_KEY,
    LM_BASE_URL,
)


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    vectors = []

    with httpx.Client(
        timeout=LLM_TIMEOUT,
        trust_env=False,
        headers={"Authorization": f"Bearer {LM_API_KEY}"},
    ) as client:
        # небольшие пачки уменьшают нагрузку на память
        for start in range(0, len(texts), 4):
            batch = texts[start:start + 4]

            response = client.post(
                f"{LM_BASE_URL}/embeddings",
                json={
                    "model": EMBEDDING_MODEL,
                    "input": batch,
                    "encoding_format": "float",
                },
            )
            response.raise_for_status()

            data = sorted(
                response.json()["data"],
                key=lambda item: item["index"],
            )

            indices = [item["index"] for item in data]
            if indices != list(range(len(batch))):
                raise ValueError("неверное число или порядок эмбеддингов")

            for item in data:
                vector = [float(value) for value in item["embedding"]]

                if not vector or not all(map(math.isfinite, vector)):
                    raise ValueError("модель вернула некорректный вектор")

                length = math.sqrt(sum(value ** 2 for value in vector))
                if length == 0:
                    raise ValueError("модель вернула нулевой вектор")

                vectors.append([value / length for value in vector])

    if len({len(vector) for vector in vectors}) != 1:
        raise ValueError("размерности векторов различаются")

    return vectors