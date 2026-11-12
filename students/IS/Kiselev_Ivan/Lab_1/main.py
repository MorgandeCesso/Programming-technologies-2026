import json
import os
import sys
import time
import urllib.request
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parent / ".env")

base_url = (os.getenv("BASE_URL") or "").rstrip("/")
api_key = os.getenv("API_KEY") or ""
model_name = (sys.argv[1] if len(sys.argv) > 1 else "") or os.getenv("MODEL_1") or ""


def openai_base(url: str) -> str:
    if url.endswith("/api/v1"):
        return url[: -len("/api/v1")] + "/v1"
    return url


def get_models(url: str, key: str) -> dict:
    request = urllib.request.Request(
        f"{url}/models",
        headers={"Authorization": f"Bearer {key}"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        print("GET", response.status, f"{url}/models")
        return json.loads(response.read().decode("utf-8"))


if __name__ == "__main__":
    if not base_url or not api_key:
        raise SystemExit("BASE_URL и API_KEY не заданы в .env")

    payload = get_models(base_url, api_key)
    print("Модели GET:")
    for item in payload.get("models") or []:
        loaded = "загружена" if item.get("loaded_instances") else "не загружена"
        print(f"  - {item.get('key')} ({loaded})")

    client = OpenAI(api_key=api_key, base_url=openai_base(base_url))
    print("Модели models.list():")
    for item in client.models.list().data:
        print(f"  - {item.id}")

    if not model_name:
        raise SystemExit("Модель не задана аргументом или в .env")

    started = time.perf_counter()
    response = client.responses.create(model=model_name, input="Я Иван")
    elapsed = time.perf_counter() - started
    print("Короткий запрос: Я Иван")
    print("Модель:", model_name)
    print("Статус:", response.status)
    print(f"Время: {elapsed:.1f} с")
    print("Ответ:", response.output_text or "")
    if not (response.output_text or "").strip():
        kinds = [getattr(item, "type", "?") for item in response.output or []]
        print("Пустой текст. Типы элементов:", ", ".join(kinds) or "нет")
