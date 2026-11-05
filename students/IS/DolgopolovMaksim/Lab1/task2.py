from openai import OpenAI
import dotenv
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY"),
)

GEMMA = "gemma-4-e4b-it"

responseG = client.responses.create(
    model=GEMMA,
    input="На складе три автомата выдают напитки (чай, кофе, случайный (кофе или чай с вероятностью 50/50)). На этикетках перепутали все. Сколько минимум монет надо бросить, чтобы гарантированно определить, где какой автомат?",
)

print("\n")
print(f"Gemma: ", responseG.output_text)
