import json
import time
from pathlib import Path
from getpass import getpass
from openai import OpenAI
from prompts import PROMPTS

MODEL = "qwen2.5-3b-instruct"  # для второй серии: "qwen2.5-1.5b-instruct"
TEMPERATURE = 0.2
MAX_TOKENS = 400

token = getpass("Введите API-токен LM Studio: ")
client = OpenAI(
    base_url="http://127.0.0.1:7000/v1",
    api_key=token,
    timeout=180.0,
    max_retries=0
)
results = []
print(f"\nТестируем модель: {MODEL}")
print(f"Температура: {TEMPERATURE}")
print(f"Максимум токенов: {MAX_TOKENS}")
print("=" * 50)

for name, prompt in PROMPTS.items():
    print(f"\nТест: {name}")
    print("Ожидаем ответ...")
    start = time.perf_counter()
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS
        )
        elapsed = time.perf_counter() - start
        answer = response.choices[0].message.content or ""
        print(f"Время ответа: {elapsed:.2f} сек.")
        print("Ответ:")
        print(answer)
        print("-" * 50)
        results.append({
            "test": name, "prompt": prompt, "answer": answer,
            "time_seconds": round(elapsed, 2)
        })
    except Exception as error:
        elapsed = time.perf_counter() - start
        print(f"Ошибка: {error}")
        results.append({
            "test": name, "prompt": prompt, "answer": None,
            "time_seconds": round(elapsed, 2), "error": str(error)
        })

Path("results").mkdir(exist_ok=True)
filename = f"results/{MODEL}_results.json"
data = {
    "model": MODEL,
    "quantization": "Q8_0",
    "temperature": TEMPERATURE,
    "max_tokens": MAX_TOKENS,
    "results": results
}
with open(filename, "w", encoding="utf-8") as file:
    json.dump(data, file, ensure_ascii=False, indent=4)
print("\nВсе тесты завершены!")
print(f"Результаты сохранены: {filename}")
