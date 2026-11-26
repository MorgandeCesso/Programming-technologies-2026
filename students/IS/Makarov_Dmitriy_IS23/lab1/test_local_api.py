import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url=os.getenv(
        "LM_STUDIO_BASE_URL",
        "http://localhost:1234/v1"
    ),
    api_key=os.getenv("LM_STUDIO_API_KEY")
)

models = client.models.list()

print("Доступные модели:")
for model in models.data:
    print("-", model.id)

if not models.data:
    raise RuntimeError("На сервере нет доступных моделей.")

MODEL = models.data[0].id

print("\nТестируем модель:", MODEL)

response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {
            "role": "user",
            "content": "Привет! Объясни, что такое Python, в двух предложениях."
        }
    ],
    max_tokens=2048
)

print("\nОтвет модели:")
print(response.choices[0].message.content)