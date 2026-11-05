
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.getenv("LM_STUDIO_BASE_URL"),
    api_key=os.getenv("LM_STUDIO_API_KEY"),
)

MODEL = os.getenv("MODEL")
models = client.models.list()

print("Доступные модели:")
for model in models.data:
    print(f" - {model.id}")

response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {
            "role": "user",
            "content": (
                "объясни, что такое переменная "
                "в Python, и приведи пример."
            ),
        }
    ],
    temperature=0.2,
)

print("\nответ модели:")
print(response.choices[0].message.content)
