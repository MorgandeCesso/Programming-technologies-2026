from openai import OpenAI
from dotenv import load_dotenv
import os
import time

load_dotenv()

client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key=os.getenv("LMSTUDIO_TOKEN"),
)

MODEL = "microsoft_phi-4-mini-instruct"

prompt = ("Извлеки данные из текста и верни ответ в формате JSON (name, age, group, email).\n"
          "Текст: Иван Петров, 21 год, группа ИС-23, почта ivan.petrov@example.com.")

for temperature in [0.2, 1.0]:
    for i in range(3):
        print(f"Температура {temperature}, попытка {i + 1}:")
        print("Ждём ответ...")
        start = time.time()
        response = client.responses.create(model=MODEL, input=prompt, temperature=temperature)
        print(response.output_text)
        print("Время:", round(time.time() - start, 2), "с")
        print("-" * 50)