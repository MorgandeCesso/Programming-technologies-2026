
import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.getenv(
        "LM_STUDIO_BASE_URL",
        "http://127.0.0.1:1234/v1"
    ),
    api_key=os.getenv("LM_STUDIO_API_KEY", "lm-studio"),
    timeout=180.0,
)

MODEL = os.getenv("MODEL")

if not MODEL:
    raise ValueError("Укажи MODEL в файле .env")

TESTS = [
    {
        "name": "1. Объяснение понятия",
        "prompt": (
            "Объясни простыми словами, что такое "
            "список в Python. Приведи один пример."
        ),
    },
    {
        "name": "2. Написание функции",
        "prompt": (
            "Напиши функцию Python sum_even(numbers), "
            "которая возвращает сумму чётных чисел "
            "из списка. Приведи пример использования."
        ),
    },
    {
        "name": "3. Поиск ошибки",
        "prompt": (
            "Найди ошибку в коде, исправь её и объясни:\n"
            "def square(x):\n"
            "    return x * x\n"
            "print(square('5'))"
        ),
    },
    {
        "name": "4. Извлечение JSON",
        "prompt": (
            "Извлеки информацию из текста и верни "
            "только корректный JSON без пояснений.\n"
            "Текст: Анна, 21 год, изучает Python "
            "и JavaScript.\n"
            "Поля JSON: name, age, languages."
        ),
    },
    {
        "name": "5. Недостаточно информации",
        "prompt": (
            "прочитай текст: Студент "
            "изучает Python и работает над проектом.\n"
            "вопрос: В каком университете он учится?\n"
            "если информации недостаточно, "
            "сообщи об этом. Не придумывай ответ."
        ),
    },
]

results = []

print(f"\nТестирование модели: {MODEL}")
print("=" * 55)

for test in TESTS:
    print(f"\n{test['name']}")

    start = time.perf_counter()

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": test["prompt"],
                }
            ],
            temperature=0.2,
            max_tokens=500,
        )

        elapsed = time.perf_counter() - start
        answer = response.choices[0].message.content or ""

        print(f"Время ответа: {elapsed:.2f} сек.")
        print(f"Ответ:\n{answer}")

        results.append({
            "test": test["name"],
            "prompt": test["prompt"],
            "answer": answer,
            "time_seconds": round(elapsed, 2),
            "temperature": 0.2,
            "status": "success",
            "finish_reason": response.choices[0].finish_reason,
        })

    except Exception as error:
        print(f"Ошибка: {error}")

        results.append({
            "test": test["name"],
            "prompt": test["prompt"],
            "answer": "",
            "time_seconds": round(
                time.perf_counter() - start, 2
            ),
            "temperature": 0.2,
            "status": "error",
            "error": str(error),
        })
output_dir = Path("results")
output_dir.mkdir(exist_ok=True)
filename = output_dir / f"{MODEL}_results.json"

with open(filename, "w", encoding="utf-8") as file:
    json.dump(results, file, ensure_ascii=False, indent=4)
print("\n" + "=" * 55)
print(f"Результаты сохранены: {filename}")
