from openai import OpenAI
from dotenv import load_dotenv
import os
import time

load_dotenv()

client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key=os.getenv("LMSTUDIO_API_KEY"),
)

MODEL = "qwen2.5-3b-instruct"
TEMPERATURE = 0.2

prompts = [
    "Объясни простыми словами, что такое переменная в программировании. Ответ дай на русском, в двух-трёх предложениях.",
    "Напиши небольшую функцию на Python, которая принимает два числа и возвращает их сумму. Добавь короткий пример вызова.",
    "Найди ошибку в коде и напиши исправленный вариант:\ndef average(a, b):\n    return a + b / 2",
    "Из текста ниже извлеки имя, группу и язык программирования. Ответ дай только в формате JSON.\nТекст: Я Студент 4 курса группы ИС-23, Артём. Мой любимый язык программирования — Python. В 2024 году я купил свой первый MacBook.",
    "По тексту ниже ответь, в каком городе живёт Артём. Если информации недостаточно, сообщи об этом.\nТекст: Я Студент 4 курса группы ИС-23, Артём. Мой любимый язык программирования — Python. В 2024 году я купил свой первый MacBook.",
]

for number, text in enumerate(prompts, 1):
    print(f"\n=== Запрос {number} ===")
    start = time.perf_counter()
    response = client.responses.create(
        model=MODEL,
        input=text,
        temperature=TEMPERATURE,
    )
    seconds = time.perf_counter() - start
    print(f"Время: {seconds:.1f} с")
    print(response.output_text)