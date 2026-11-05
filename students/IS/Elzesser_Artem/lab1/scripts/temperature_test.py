import json
import time
from pathlib import Path
from getpass import getpass
from openai import OpenAI
from prompts import PROMPTS

MODEL = "qwen2.5-1.5b-instruct"
MAX_TOKENS = 400
PROMPT = PROMPTS["1_concept"]
token = getpass("Введите API-токен LM Studio: ")
client = OpenAI(
    base_url="http://127.0.0.1:7000/v1",
    api_key=token,
    timeout=180.0,
    max_retries=0
)
results = []
for temperature in [0.2, 1.0]:
    for run in range(1, 4):
        print(f"\nТемпература: {temperature}, запуск: {run}")
        print("Ожидаем ответ...")
        start = time.perf_counter()
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": PROMPT}],
                temperature=temperature,
                max_tokens=MAX_TOKENS
            )
            elapsed = round(time.perf_counter() - start, 2)
            answer = response.choices[0].message.content or ""
            finish_reason = response.choices[0].finish_reason
            print(f"Время: {elapsed} сек.")
            print(f"Причина завершения: {finish_reason}")
            print("Ответ:")
            print(answer)
            print("-" * 50)
            results.append({
                "temperature": temperature, "run": run,
                "time_seconds": elapsed, "answer": answer,
                "finish_reason": finish_reason
            })
        except Exception as error:
            elapsed = round(time.perf_counter() - start, 2)
            print(f"Ошибка: {error}")
            results.append({
                "temperature": temperature, "run": run,
                "time_seconds": elapsed, "error": str(error)
            })
Path("results").mkdir(exist_ok=True)
data = {
    "model": MODEL,
    "quantization": "Q8_0",
    "prompt": PROMPT,
    "max_tokens": MAX_TOKENS,
    "results": results
}
filename = "results/temperature_results.json"
with open(filename, "w", encoding="utf-8") as file:
    json.dump(data, file, ensure_ascii=False, indent=4)
print("\nЭксперимент завершён!")
print(f"Результаты сохранены: {filename}")
