from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key=os.getenv("LMSTUDIO_API_KEY"),
)

MODEL = "llama-3.2-3b-instruct"

models = client.models.list()
print("Модели:")
for model in models.data:
    print(f"  - {model.id}")

response = client.responses.create(
    model=MODEL,
    input="Я Артём",
)
print()
print(response.output_text)