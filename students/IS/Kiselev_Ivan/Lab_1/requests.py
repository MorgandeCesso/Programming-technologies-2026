import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parent / ".env")

base_url = (os.getenv("BASE_URL") or "").rstrip("/")
api_key = os.getenv("API_KEY") or ""
temperature = float(os.getenv("TEMPERATURE") or "0.7")

PROMPTS = [
    (
        "Понятие",
        "Объясни простыми словами, что такое хеш-таблица и чем она отличается от списка. Кратко, на русском.",
    ),
    (
        "Функция",
        "Напиши функцию на Python even_numbers(nums), которая принимает список чисел и возвращает новый список только из чётных чисел, сохраняя исходный порядок. Без пояснений вокруг кода.",
    ),
    (
        "Ошибка в коде",
        "Найди ошибку в коде и напиши, в каком случае функция вернёт неверный результат.\n"
        "def find_max(nums):\n"
        "    best = 0\n"
        "    for n in nums:\n"
        "        if n > best:\n"
        "            best = n\n"
        "    return best",
    ),
    (
        "JSON",
        "Текст: Студент Иван сдал лабораторную 12 марта 2026 года. Язык решения - Python, оценка - 5.\n"
        "Извлеки данные и ответь только JSON с ключами name, date, language, grade. Не добавляй текст вокруг JSON.",
    ),
    (
        "Нет ответа в тексте",
        "Текст: Студент Иван сдал лабораторную 12 марта 2026 года. Язык решения - Python, оценка - 5.\n"
        "Какой редактор кода использовал студент? Если информации недостаточно, сообщи об этом.",
    ),
]


def openai_base(url: str) -> str:
    if url.endswith("/api/v1"):
        return url[: -len("/api/v1")] + "/v1"
    return url


def ask(client: OpenAI, model: str, prompt: str) -> tuple[float, str]:
    started = time.perf_counter()
    response = client.responses.create(
        model=model,
        input=prompt,
        temperature=temperature,
    )
    elapsed = time.perf_counter() - started
    return elapsed, (response.output_text or "").strip()


if __name__ == "__main__":
    if not base_url or not api_key:
        raise SystemExit("BASE_URL и API_KEY не заданы в .env")

    models = sys.argv[1:]
    if not models:
        models = [name for name in (os.getenv("MODEL_1"), os.getenv("MODEL_2")) if name]
    if not models:
        raise SystemExit("Модель не задана аргументом или в .env")

    client = OpenAI(api_key=api_key, base_url=openai_base(base_url))
    print(f"temperature = {temperature}")

    for model in models:
        print(f"\nМодель: {model} с температурой {temperature}")
        for index, (title, prompt) in enumerate(PROMPTS, start=1):
            try:
                elapsed, answer = ask(client, model, prompt)
            except Exception as exc:
                print(f"{index}. {title}: ошибка: {exc}")
                continue
            print(f"{index}. {title}: {elapsed:.1f} с")
            print(answer or "Пустой ответ")
            print()
