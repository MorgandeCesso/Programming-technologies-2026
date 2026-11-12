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

MODELS = ["gemma 4 e4b"]
TEMPERATURE = 0.2

note = (
    "Я студент 4 курса группы ИС-23, Никита. "
    "Мой любимый язык программирования — Python. "
    "В 2024 году я купил свой первый MacBook."
)

prompts = [
    "Объясни простыми словами, что такое переменная в программировании. Ответ дай на русском, в двух-трёх предложениях.",
    "Напиши небольшую функцию на Python, которая принимает два числа и возвращает их сумму. Добавь короткий пример вызова.",
    "Найди ошибку в коде и напиши исправленный вариант:\ndef average(a, b):\n    return a + b / 2",
    "Из текста ниже извлеки имя, группу и язык программирования. Ответ дай только в формате JSON.\nТекст: " + note,
    "По тексту ниже ответь, в каком городе живёт Никита. Если информации недостаточно, сообщи об этом.\nТекст: " + note,
]

for model in MODELS:
    print(f"\n##### {model} #####")
    for number, text in enumerate(prompts, 1):
        print(f"\n=== Запрос {number} ===")
        start = time.perf_counter()
        response = client.responses.create(
            model=model,
            input=text,
            temperature=TEMPERATURE,
        )
        seconds = time.perf_counter() - start
        print(f"Время: {seconds:.1f} с")
        print(response.output_text)
