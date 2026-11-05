
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

PROMPT = (
    "Напиши функцию Python, которая определяет, "
    "является ли число простым. "
    "Объясни алгоритм и приведи пример использования."
)
TEMPERATURES = [0.2, 1.0]
REPEATS = 3
results = []

print(f"Модель: {MODEL}")
print("Исследование влияния температуры")
print("=" * 55)

for temperature in TEMPERATURES:

    print(f"\nТемпература: {temperature}")
    print("-" * 55)

    for attempt in range(1, REPEATS + 1):

        print(f"\nЗапуск №{attempt}")

        start = time.perf_counter()

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": PROMPT,
                    }
                ],
                temperature=temperature,
                max_tokens=700,
            )

            elapsed = time.perf_counter() - start

            answer = (
                response.choices[0].message.content or ""
            )

            print(f"Время ответа: {elapsed:.2f} сек.")
            print(f"Ответ модели:\n{answer}")

            results.append({
                "model": MODEL,
                "temperature": temperature,
                "attempt": attempt,
                "prompt": PROMPT,
                "answer": answer,
                "time_seconds": round(elapsed, 2),
                "status": "success",
                "finish_reason": response.choices[0].finish_reason,
            })

        except Exception as error:

            print(f"Ошибка: {error}")

            results.append({
                "model": MODEL,
                "temperature": temperature,
                "attempt": attempt,
                "prompt": PROMPT,
                "answer": "",
                "time_seconds": round(
                    time.perf_counter() - start, 2
                ),
                "status": "error",
                "error": str(error),
            })

output_dir = Path("results")
output_dir.mkdir(exist_ok=True)
filename = output_dir / f"{MODEL}_temperature_results.json"

with open(filename, "w", encoding="utf-8") as file:
    json.dump(
        results,
        file,
        ensure_ascii=False,
        indent=4
    )

print("\n" + "=" * 55)
print("Эксперимент завершён!")
print(f"Результаты сохранены: {filename}")
