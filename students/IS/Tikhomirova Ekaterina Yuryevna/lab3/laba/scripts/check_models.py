import os
from pathlib import Path

import httpx
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def main():
    base_url = os.getenv(
        "LM_BASE_URL", "http://127.0.0.1:1234/v1"
    ).rstrip("/")
    api_key = os.getenv("LM_API_KEY", "lm-studio")
    model = os.getenv("EMBEDDING_MODEL", "text-embedding-bge-m3")

    with httpx.Client(
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=120,
        trust_env=False,
    ) as client:
        response = client.post(
            f"{base_url}/embeddings",
            json={
                "model": model,
                "input": ["датчик передает значения температуры"],
                "encoding_format": "float",
            },
        )
        response.raise_for_status()

        vector = response.json()["data"][0]["embedding"]
        print("эмбеддинг получен")
        print("размерность:", len(vector))
        print("первые пять значений:", vector[:5])


if __name__ == "__main__":
    try:
        main()
    except httpx.HTTPStatusError as error:
        print("ошибка HTTP:", error.response.status_code)
        print("проверь ключ в .env и загрузку модели")
    except httpx.RequestError:
        print("нет ответа от LM Studio: проверь запуск сервера")
        