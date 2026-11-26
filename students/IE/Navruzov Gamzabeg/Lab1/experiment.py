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

MODEL = "qwen2.5-3b-instruct"  # или "llama-3.2-3b-instruct"
#MODEL = "llama-3.2-3b-instruct"
TEMPERATURE = 0.3

prompts = [
    "Объясни простыми словами, что такое рекурсия в программировании, и приведи короткий пример.",
    "Напиши функцию на Python, которая принимает список чисел и возвращает новый список только с чётными числами, отсортированный по убыванию.",
    "Найди ошибку в следующем коде на Python и покажи исправленный вариант:\n\ndef average(numbers):\n    total = 0\n    for i in range(1, len(numbers)):\n        total += numbers[i]\n    return total / len(numbers)",
    "Извлеки из текста имя, возраст, город и профессию. Верни ответ строго в формате JSON без лишнего текста.\nТекст: «Меня зовут Анна Смирнова, мне 28 лет. Я живу в Казани и работаю аналитиком данных в банке.»",
    "Ответь на вопрос по тексту. Если информации недостаточно, сообщи об этом.\nТекст: «Сервер был перезапущен в 14:30 для обновления безопасности. Работа восстановилась через 5 минут.»\nВопрос: Какая версия операционной системы установлена на сервере?",
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
    print(f"Время: {seconds:.2f} с")
    print(response.output_text)
