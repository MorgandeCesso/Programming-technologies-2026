from getpass import getpass
from openai import OpenAI

token = getpass("Введите API-токен LM Studio: ")
client = OpenAI(
    base_url="http://127.0.0.1:7000/v1",
    api_key=token,
    timeout=120.0
)
MODEL = "qwen2.5-1.5b-instruct"  # для второй проверки: qwen2.5-3b-instruct

print("Доступные модели:")
models = client.models.list()
for model in models.data:
    print(" -", model.id)

print("\nОтправляем запрос модели...")
response = client.chat.completions.create(
    model=MODEL,
    messages=[{"role": "user", "content": "Объясни одним предложением, что такое Python."}],
    temperature=0.2,
    max_tokens=120
)
print("\nОтвет модели:")
print(response.choices[0].message.content)
