from openai import OpenAI
from dotenv import load_dotenv
import os
import time

load_dotenv()

client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key=os.getenv("LMSTUDIO_TOKEN"),
)

MODEL = "qwen_qwen3.5-4b"

prompts = [
    "Объясни простыми словами, что такое рекурсия в программировании.",
    "Напиши функцию на Python, которая проверяет, является ли строка палиндромом.",
    "Найди ошибку в коде:\n"
    "def average(numbers):\n"
    "    total = 0\n"
    "    for i in range(1, len(numbers)):\n"
    "        total += numbers[i]\n"
    "    return total / len(numbers)",
    "Извлеки данные из текста и верни ответ в формате JSON (name, age, group, email).\n"
    "Текст: Иван Петров, 21 год, группа ИС-23, почта ivan.petrov@example.com.",
    "Компания «ТехСофт» основана в 2015 году в Новосибирске. "
    "Какую прибыль получила компания в 2023 году? Если информации недостаточно, сообщи об этом.",
]

for prompt in prompts:
    print("Вопрос:", prompt)
    print("Ждём ответ...")
    start = time.time()
    response = client.responses.create(model=MODEL, input=prompt)
    print("Ответ:", response.output_text)
    print("Время:", round(time.time() - start, 2), "с")
    print("-" * 50)