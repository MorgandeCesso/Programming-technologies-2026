from openai import OpenAI
import dotenv
from dotenv import load_dotenv
import os

load_dotenv()

with open('task3.txt', 'r', encoding='utf-8') as file:
    Task3 = file.read()

with open('task4.txt', 'r', encoding='utf-8') as file:
    Task4 = file.read()

with open('task5.txt', 'r', encoding='utf-8') as file:
    Task5 = file.read()

client = OpenAI(base_url=os.getenv("BASE_URL"),api_key=os.getenv("API_KEY"))

GEMMA = "gemma-4-e4b-it"
QWEN = "qwen3.5-4b@q4_k_m"

Task1 = "Что такое SOLID в ООП и что в себя включает"
Task2 = "Напиши функцию счетчика на языке программирования Python"

Tasks = [Task1, Task2, Task3, Task4, Task5]
counter = 0
tcounter = counter
while counter < 5:

    print("\n")
    tcounter += 1
    print(f"Задача {tcounter}: \n")
    print(f"Gemma: ", client.responses.create(model=GEMMA, input=Tasks[counter]).output_text)

    print("\n")
    print(f"Qwen: ", client.responses.create(model=QWEN, input=Tasks[counter]).output_text)
    counter += 1
