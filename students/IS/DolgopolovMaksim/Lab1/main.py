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
QWEN = "qwen3.5-4b"

models = client.models.list()
print("Модели:")
for model in models.data:
    print(f"  - {model.id}")

responseG = client.responses.create(
    model=GEMMA,
    input="Я Максим",
)

responseQ = client.responses.create(
    model=QWEN,
    input="Я Максим",
)
print("\n")
print(f"Gemma: ", responseG.output_text)
print("\n")
print(f"Qwen: ", responseQ.output_text)