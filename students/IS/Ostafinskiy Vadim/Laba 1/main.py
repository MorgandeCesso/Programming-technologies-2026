
import os
import time
import json

from datetime import datetime
from pathlib import Path
from prompts import PROMPTS
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.getenv("LM_STUDIO_BASE_URL"),
    api_key=os.getenv("LM_STUDIO_API_KEY"),
)

MODEL = "qwen3.5-9b"
TEMPERATURE = 1.0
CONTEXT_LENGTH = 2048
QUANTIZATION = "Q4_K_M"

def manual_mode():
    print("\nРучной режим. Для выхода в меню введите 'exit'.")

    while True:
        question = input("\nВведите вопрос: ").strip()

        if question.lower() == "exit":
            break

        if not question:
            print("Вопрос не может быть пустым.")
            continue

        response = client.responses.create(
            model=MODEL,
            input=question,
            temperature=TEMPERATURE,
        )

        print("\nОтвет модели:")
        print(response.output_text)



def test_mode():
    print(f"\nЗапуск тестов для {MODEL}")

    results = []

    for test in PROMPTS:
        print(f"\nТест №{test['id']}: {test['name']}")
        print(f"Запрос: {test['prompt']}")

        start_time = time.perf_counter()

        response = client.responses.create(
            model=MODEL,
            input=test["prompt"],
            temperature=TEMPERATURE,
        )

        elapsed_time = time.perf_counter() - start_time

        answer = response.output_text

        print("\nОтвет модели:")
        print(answer)

        print(f"\nВремя полного ответа: {elapsed_time:.2f} сек.")
        print("-" * 60)

        results.append({
            "model": MODEL,
            "temperature": TEMPERATURE,
            "context_length": CONTEXT_LENGTH,
            "quantization": QUANTIZATION,
            "test_id": test["id"],
            "test_name": test["name"],
            "prompt": test["prompt"],
            "answer": answer,
            "elapsed_time": round(elapsed_time, 2),
        })

    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = results_dir / f"{MODEL}_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(results, file, ensure_ascii=False, indent=4)

    print(f"\nРезультаты сохранены в файл: {filename}")


def temperature_test():
    test = PROMPTS[1]

    temperatures = [0.2, 1.0]
    results = []

    print(f"\nИсследование температуры для {MODEL}")
    print(f"Тест: {test['name']}")

    for temperature in temperatures:
        for attempt in range(1, 4):
            print(f"\nТемпература: {temperature}, повторение: {attempt}")

            start_time = time.perf_counter()

            response = client.responses.create(
                model=MODEL,
                input=test["prompt"],
                temperature=temperature,
            )

            elapsed_time = time.perf_counter() - start_time
            answer = response.output_text

            print("\nОтвет модели:")
            print(answer)
            print(f"\nВремя: {elapsed_time:.2f} сек.")

            results.append({
                "model": MODEL,
                "temperature": temperature,
                "context_length": CONTEXT_LENGTH,
                "quantization": QUANTIZATION,
                "attempt": attempt,
                "test_id": test["id"],
                "prompt": test["prompt"],
                "answer": answer,
                "elapsed_time": round(elapsed_time, 2),
            })

    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = results_dir / f"{MODEL}_temperature_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(results, file, ensure_ascii=False, indent=4)

    print(f"\nРезультаты эксперимента сохранены: {filename}")


def main():
    models = client.models.list()

    print("Доступные модели:")
    for model in models.data:
        print(f"  - {model.id}")

    while True:
        print("\nВыберите режим работы:")
        print("1. Ручной ввод вопросов")
        print("2. Тесты")
        print("3. Исследование температуры")
        print("0. Выход")

        choice = input("\nВаш выбор: ").strip()

        if choice == "1":
            manual_mode()

        elif choice == "2":
            test_mode()

        elif choice == "3":
            temperature_test()    

        elif choice == "0":
            print("Программа завершена.")
            break

        else:
            print("Неверный выбор. Попробуйте снова.")


if __name__ == "__main__":
    main()
