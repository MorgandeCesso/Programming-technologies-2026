import os
import json
import time
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.getenv(
        "LM_STUDIO_BASE_URL",
        "http://localhost:1234/v1"
    ),
    api_key=os.getenv("LM_STUDIO_API_KEY"),
    timeout=300.0
)

MODELS = [
    "qwen3.5-4b",
    "qwen/qwen3-8b"
]

TEMPERATURE = 0.2
MAX_TOKENS = 2048

TESTS = [
    {
        "id": 1,
        "name": "Объяснение понятия",
        "prompt": (
            "Объясни начинающему программисту, "
            "что такое рекурсия в Python. "
            "Приведи простой пример. "
            "Ответь кратко."
        )
    },
    {
        "id": 2,
        "name": "Написание функции",
        "prompt": (
            "Напиши функцию Python is_prime(n), "
            "которая возвращает True, если число n простое, "
            "и False в остальных случаях. "
            "Приведи код и краткое объяснение."
        )
    },
    {
        "id": 3,
        "name": "Поиск ошибки",
        "prompt": (
            "Найди ошибку в следующем коде Python, "
            "объясни её и предложи исправленный код:\n\n"
            "def average(numbers):\n"
            "    return sum(numbers) / len(numbers)\n\n"
            "print(average([]))"
        )
    },
    {
        "id": 4,
        "name": "Извлечение информации в JSON",
        "prompt": (
            "Извлеки информацию из текста и верни "
            "только корректный JSON без Markdown.\n\n"
            "Текст: Анна Иванова работает Python-разработчиком "
            "в компании ТехноСофт. Ей 25 лет. "
            "Она живёт в Казани.\n\n"
            "Формат JSON:\n"
            '{"name": "...", "age": 0, '
            '"city": "...", "company": "...", '
            '"position": "..."}'
        )
    },
    {
        "id": 5,
        "name": "Недостаточно информации",
        "prompt": (
            "Прочитай текст и ответь на вопрос. "
            "Если информации недостаточно, сообщи об этом.\n\n"
            "Текст: Компания Альфа была основана в 2015 году. "
            "Она занимается разработкой мобильных приложений. "
            "В компании работают 50 сотрудников.\n\n"
            "Вопрос: Кто является генеральным директором компании?"
        )
    }
]


def run_test(model, test):
    print(f"\nТест {test['id']}: {test['name']}")

    start = time.perf_counter()

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты помощник по программированию. "
                        "Отвечай на русском языке. "
                        "Соблюдай формат, указанный в запросе."
                    )
                },
                {
                    "role": "user",
                    "content": test["prompt"] + "\n/no_think"
                }
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS
        )

        elapsed = time.perf_counter() - start

        answer = response.choices[0].message.content or ""

        print(f"Время: {elapsed:.2f} сек.")
        print("Ответ:")
        print(answer if answer else "[Пустой ответ]")

        return {
            "test_id": test["id"],
            "test_name": test["name"],
            "model": model,
            "temperature": TEMPERATURE,
            "time_seconds": round(elapsed, 2),
            "answer": answer,
            "finish_reason": response.choices[0].finish_reason,
            "error": None
        }

    except Exception as error:
        elapsed = time.perf_counter() - start

        print("Ошибка:", error)

        return {
            "test_id": test["id"],
            "test_name": test["name"],
            "model": model,
            "temperature": TEMPERATURE,
            "time_seconds": round(elapsed, 2),
            "answer": "",
            "finish_reason": None,
            "error": str(error)
        }


def main():
    available = {
        model.id for model in client.models.list().data
    }

    results = []

    for model in MODELS:
        if model not in available:
            print(f"Модель {model} не найдена на сервере.")
            continue

        print("\n" + "=" * 60)
        print("МОДЕЛЬ:", model)
        print("=" * 60)

        input(
            "Убедись, что эта модель загружена в LM Studio. "
            "Нажми Enter для начала тестов..."
        )

        for test in TESTS:
            result = run_test(model, test)
            results.append(result)

    filename = (
        "comparison_"
        + datetime.now().strftime("%Y%m%d_%H%M%S")
        + ".json"
    )

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(results, file, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("Результаты сохранены в:", filename)

    print("\nСравнение времени:")

    for result in results:
        print(
            f"{result['model']} | "
            f"Тест {result['test_id']} | "
            f"{result['time_seconds']} сек."
        )


if __name__ == "__main__":
    main()