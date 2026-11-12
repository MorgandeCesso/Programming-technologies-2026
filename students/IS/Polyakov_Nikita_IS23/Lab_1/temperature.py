from openai import OpenAI
from dotenv import load_dotenv
import os
import time

load_dotenv()

client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key=os.getenv("LMSTUDIO_API_KEY"),
    timeout=180.0,
)

MODEL = "gemma 4 e4b"
prompt = "Объясни простыми словами, что такое переменная в программировании. Ответ дай на русском, в двух-трёх предложениях."

for temperature in (0.2, 1.0):
    for attempt in (1, 2, 3):
        print(f"\n=== temperature {temperature}, попытка {attempt} ===")
        start = time.perf_counter()
        response = client.responses.create(
            model=MODEL,
            input=prompt,
            temperature=temperature,
        )
        seconds = time.perf_counter() - start
        print(f"Время: {seconds:.1f} с")
        print(response.output_text)
