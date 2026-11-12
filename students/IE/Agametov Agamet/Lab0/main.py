from openai import OpenAI, OpenAIError
from dotenv import load_dotenv
import os
import sqlite3

load_dotenv()

api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL", "https://api.groq.com/openai/v1")
model = os.getenv("MODEL", "openai/gpt-oss-20b")
env_prompt = os.getenv("SYSTEM_PROMPT", "Ты полезный ассистент.")

client = OpenAI(api_key=api_key, base_url=base_url)

db = sqlite3.connect("prompts.db")
db.execute("CREATE TABLE IF NOT EXISTS prompts (id INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT NOT NULL)")
db.commit()


def get_response(messages, client: OpenAI, system_prompt, effort, temperature):
    params = {
        "model": model,
        "instructions": system_prompt,
        "input": messages,
    }
    if effort:
        params["reasoning"] = {"effort": effort}
    if temperature is not None:
        params["temperature"] = temperature
    return client.responses.create(**params)


def choose_prompt():
    print("Системный промпт:")
    print("1 - из .env")
    print("2 - выбрать из базы")
    print("3 - написать новый и сохранить в базу")
    choice = input("> ").strip()

    if choice == "2":
        rows = db.execute("SELECT id, text FROM prompts").fetchall()
        for prompt_id, text in rows:
            print(f"{prompt_id}. {text}")
        number = input("Номер: ").strip()
        row = db.execute("SELECT text FROM prompts WHERE id = ?", (number,)).fetchone()
        if row:
            return row[0]
        print("Такого промпта нет, беру из .env")

    if choice == "3":
        text = input("Текст промпта: ").strip()
        if text:
            db.execute("INSERT INTO prompts (text) VALUES (?)", (text,))
            db.commit()
            print("Промпт сохранен в базу")
            return text

    return env_prompt


if __name__ == "__main__":
    system_prompt = choose_prompt()
    effort = None
    temperature = None
    history = []

    print("Введите ваш вопрос (или 'exit' для выхода)")
    print("Команды: /prompt, /effort, /temp, /history, /clear")

    while True:
        question = input("Вы: ").strip()

        if not question:
            continue

        if question.lower() == "exit":
            print("Завершение программы.")
            break

        if question == "/prompt":
            system_prompt = choose_prompt()
            continue

        if question == "/effort":
            effort = input("low, medium или high (пусто - по умолчанию): ").strip() or None
            continue

        if question == "/temp":
            value = input("например 0, 0.7, 1.5 (пусто - по умолчанию): ").strip()
            temperature = float(value) if value else None
            continue

        if question == "/history":
            for message in history:
                print(f"{message['role']}: {message['content']}")
            continue

        if question == "/clear":
            history = []
            print("История очищена")
            continue

        messages = history + [{"role": "user", "content": question}]

        try:
            response = get_response(messages, client, system_prompt, effort, temperature)
        except OpenAIError as e:
            print("Ошибка:", e)
            continue

        answer = response.output_text
        print("AI:", answer)
        print(f"(токенов в ответе: {response.usage.output_tokens})")

        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": answer})
        history = history[-6:]
