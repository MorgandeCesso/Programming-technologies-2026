from openai import OpenAI, BadRequestError
from dotenv import load_dotenv
import os
import sqlite3
import time

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
env_prompt = os.getenv("SYSTEM_PROMPT", "Ты полезный ассистент.")

client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")

DB_PATH = "prompts.db"
MAX_HISTORY = 6  


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS prompts ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "name TEXT NOT NULL, "
            "text TEXT NOT NULL)"
        )


def add_prompt(name: str, text: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT INTO prompts (name, text) VALUES (?, ?)", (name, text))


def list_prompts():
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute("SELECT id, name, text FROM prompts").fetchall()


def get_prompt(prompt_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute(
            "SELECT name, text FROM prompts WHERE id = ?", (prompt_id,)
        ).fetchone()


def get_response(messages, client: OpenAI, instructions: str, effort=None, temperature=None):
    params = {
        "model": "openai/gpt-oss-20b",
        "instructions": instructions,
        "input": messages,  
    }
    if effort is not None:
        params["reasoning"] = {"effort": effort}
    if temperature is not None:
        params["temperature"] = temperature
    return client.responses.create(**params)



if __name__ == "__main__":
    init_db()
    current_name = "из .env"
    current_prompt = env_prompt
    effort = None
    temperature = None
    history = [] 

    print("Команды: /add, /prompts, /use N, /env, /effort X, /temp X, /history, /clear, exit")
    print(f"Текущий промпт: {current_name}")

    while True:
        question = input("Вы: ").strip()

        if not question: 
            continue

        if question.lower() == "exit":
            print("Завершение программы.")
            break

        if question == "/add":
            name = input("Название промпта: ").strip()
            text = input("Текст промпта: ").strip()
            add_prompt(name, text)
            print("Промпт сохранён в базу.")
            continue

        if question == "/prompts":
            for pid, name, text in list_prompts():
                print(f"  [{pid}] {name}: {text}")
            continue

        if question.startswith("/use "):
            prompt_id = question.split()[1]
            found = get_prompt(int(prompt_id)) if prompt_id.isdigit() else None
            if found:
                current_name, current_prompt = found
                print(f"Промпт переключён на: {current_name}")
            else:
                print("Нет такого промпта. Посмотри список: /prompts")
            continue

        if question == "/env":
            current_name, current_prompt = "из .env", env_prompt
            print("Вернулись к промпту из .env")
            continue

        if question.startswith("/effort "):
            value = question.split()[1]
            effort = None if value == "off" else value
            print(f"reasoning.effort = {effort or 'по умолчанию'}")
            continue

        if question.startswith("/temp "):
            value = question.split()[1]
            temperature = None if value == "off" else float(value)
            print(f"temperature = {temperature if temperature is not None else 'по умолчанию'}")
            continue

        if question == "/history": 
            for msg in history:
                print(f"  {msg['role']}: {msg['content'][:60]}")
            print(f"  (всего сообщений: {len(history)})")
            continue

        if question == "/clear":  
            history = []
            print("История очищена.")
            continue

        messages = history + [{"role": "user", "content": question}]

        try:
            start = time.time()
            answer = get_response(messages, client, current_prompt, effort, temperature)
            elapsed = time.time() - start
        except BadRequestError as e:
            print("Ошибка запроса:", e)
            continue

        print("AI:", answer.output_text)
        print(f"[время: {elapsed:.1f} с, токенов в ответе: {answer.usage.output_tokens}]")


        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": answer.output_text})
        history = history[-MAX_HISTORY:]