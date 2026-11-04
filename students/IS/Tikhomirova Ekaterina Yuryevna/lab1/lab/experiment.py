import json
import os
from datetime import datetime
from pathlib import Path
from time import perf_counter

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError


ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env", override=True)

SYSTEM_PROMPT = (
    "отвечай на русском языке. следуй требованиям запроса. "
    "при работе с предоставленным текстом используй только его сведения. "
    "если информации недостаточно, сообщи об этом."
)

TASKS = [
    {
        "id": "01_concept",
        "prompt": (
            "объясни, что такое список в Python. "
            "ответь в двух предложениях и приведи один короткий пример."
        ),
    },
    {
        "id": "02_function",
        "prompt": (
            "напиши функцию sum_even(numbers) на Python, которая возвращает "
            "сумму четных целых чисел из списка. для пустого списка верни 0. "
            "ответ должен содержать только код функции без Markdown."
        ),
    },
    {
        "id": "03_debug",
        "prompt": (
            "найди ошибку в коде. он должен возвращать сумму всех чисел списка. "
            "кратко объясни ошибку и приведи исправленный код.\n\n"
            "def total(numbers):\n"
            "    result = 0\n"
            "    for n in numbers:\n"
            "        result += n\n"
            "        return result\n"
        ),
    },
    {
        "id": "04_json",
        "prompt": (
            "извлеки данные из текста. верни только JSON-объект "
            "с ключами name, age, city. значение age должно быть числом. "
            "не добавляй Markdown и пояснения.\n\n"
            "текст: Анне 22 года. она живет в Казани."
        ),
    },
    {
        "id": "05_missing_information",
        "prompt": (
            "ответь только по предоставленному тексту. "
            "если информации недостаточно, сообщи об этом.\n\n"
            "текст: библиотека работает с понедельника по пятницу "
            "с 09:00 до 18:00. по субботам и воскресеньям она закрыта.\n\n"
            "вопрос: сколько стоит годовой абонемент в библиотеку?"
        ),
    },
]


def main():
    api_key = os.getenv("LMSTUDIO_API_KEY")

    if not api_key:
        print("укажи LMSTUDIO_API_KEY в .env.")
        return

    model = os.getenv("LMSTUDIO_MODEL", "qwen2.5-1.5b-instruct")

    client = OpenAI(
        api_key=api_key,
        base_url=os.getenv(
            "LMSTUDIO_BASE_URL",
            "http://127.0.0.1:1234/v1",
        ),
        timeout=180.0,
        max_retries=0,
    )

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output_dir = ROOT / "results" / run_id
    output_dir.mkdir(parents=True)

    print(f"модель: {model}")
    print("температура: 0.2")
    print(f"папка результатов: {output_dir}")

    print("\nпрогрев модели...")
    try:
        client.responses.create(
            model=model,
            input="ответь одним словом: привет.",
            temperature=0.2,
            max_output_tokens=32,
        )
    except OpenAIError as error:
        print(f"ошибка прогрева: {error}")
        return

    for task in TASKS:
        print(f"\nЗадание: {task['id']}")
        print("запрос:", task["prompt"])
        print("ожидаем ответ...")

        result = {
            "task_id": task["id"],
            "requested_model": model,
            "system_prompt": SYSTEM_PROMPT,
            "prompt": task["prompt"],
            "temperature": 0.2,
            "max_output_tokens": 512,
        }

        start = perf_counter()

        try:
            response = client.responses.create(
                model=model,
                instructions=SYSTEM_PROMPT,
                input=task["prompt"],
                temperature=0.2,
                max_output_tokens=512,
            )

            result.update({
                "elapsed_seconds": round(perf_counter() - start, 3),
                "response_model": response.model,
                "status": response.status,
                "answer": response.output_text,
                "usage": (
                    response.usage.model_dump()
                    if response.usage else None
                ),
                "incomplete_details": (
                    response.incomplete_details.model_dump()
                    if response.incomplete_details else None
                ),
            })

            print("\nОтвет:", result["answer"])
            print(f"время: {result['elapsed_seconds']} с")
            print(f"статус: {result['status']}")

        except OpenAIError as error:
            result.update({
                "elapsed_seconds": round(perf_counter() - start, 3),
                "status": "error",
                "error": str(error),
            })
            print("ошибка API:", error)

        file_path = output_dir / f"{task['id']}.json"
        file_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    print("\nпроверка завершена. результаты сохранены.")


if __name__ == "__main__":
    main()