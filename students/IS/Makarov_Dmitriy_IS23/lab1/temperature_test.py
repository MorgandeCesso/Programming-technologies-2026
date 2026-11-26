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

MODEL = "qwen/qwen3-8b"
TEMPERATURES = [0.2, 1.0]
REPEATS = 3
MAX_TOKENS = 2048

PROMPT = (
    "Придумай ровно 5 оригинальных названий для "
    "IT-компании. Верни только нумерованный список "
    "из пяти названий, без объяснений. /no_think"
)

results = []

for temperature in TEMPERATURES:
    print("\n" + "=" * 60)
    print(f"TEMPERATURE = {temperature}")
    print("=" * 60)

    for attempt in range(1, REPEATS + 1):
        print(f"\nПопытка {attempt} из {REPEATS}")

        start = time.perf_counter()

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Ты помощник по генерации названий. "
                            "Отвечай на русском языке. "
                            "Строго соблюдай формат ответа."
                        )
                    },
                    {
                        "role": "user",
                        "content": PROMPT
                    }
                ],
                temperature=temperature,
                max_tokens=MAX_TOKENS
            )

            elapsed = time.perf_counter() - start
            answer = response.choices[0].message.content or ""

            print(f"Время: {elapsed:.2f} сек.")
            print("Ответ:")
            print(answer if answer else "[Пустой ответ]")

            results.append({
                "model": MODEL,
                "temperature": temperature,
                "attempt": attempt,
                "time_seconds": round(elapsed, 2),
                "answer": answer,
                "finish_reason": response.choices[0].finish_reason,
                "error": None
            })

        except Exception as error:
            elapsed = time.perf_counter() - start

            print("Ошибка:", error)

            results.append({
                "model": MODEL,
                "temperature": temperature,
                "attempt": attempt,
                "time_seconds": round(elapsed, 2),
                "answer": "",
                "finish_reason": None,
                "error": str(error)
            })

filename = (
    "temperature_results_"
    + datetime.now().strftime("%Y%m%d_%H%M%S")
    + ".json"
)

with open(filename, "w", encoding="utf-8") as file:
    json.dump(results, file, ensure_ascii=False, indent=2)

print("\nЭксперимент завершён.")
print("Результаты сохранены в:", filename)