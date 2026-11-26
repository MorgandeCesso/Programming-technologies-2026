import os
import time

os.environ["NO_PROXY"] = "127.0.0.1,localhost"
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key=os.getenv("LMSTUDIO_API_KEY"),
)

MODEL = "qwen2.5-3b-instruct"
prompt = "Объясни простыми словами, что такое рекурсия в программировании, и приведи короткий пример."

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
        print(f"Время: {seconds:.2f} с")
        print(response.output_text)
