from openai import OpenAI
from dotenv import load_dotenv
import os
import sqlite3

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key, base_url=os.getenv("OPENAI_BASE_URL"))

MODEL = os.getenv("MODEL", "gpt-6-luna")


# Задание 1 

db = sqlite3.connect("prompts.db")
db.execute("CREATE TABLE IF NOT EXISTS prompts (id INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT)")
db.commit()


def save_prompt(text: str):
    db.execute("INSERT INTO prompts (text) VALUES (?)", (text,))
    db.commit()


def show_prompts():
    rows = db.execute("SELECT id, text FROM prompts").fetchall()
    if not rows:
        print("В базе пока нет промптов.")
    for prompt_id, text in rows:
        print(f"{prompt_id}: {text}")


def load_prompt(prompt_id: str):
    row = db.execute("SELECT text FROM prompts WHERE id = ?", (prompt_id,)).fetchone()
    return row[0] if row else None


def choose_prompt():
    print("\nВыберите системный промпт:")
    print("1 - из .env")
    print("2 - выбрать из базы данных")
    print("3 - ввести новый (сохранится в базу)")
    choice = input("Ваш выбор: ")

    if choice == "2":
        show_prompts()
        prompt = load_prompt(input("Номер промпта: "))
        if prompt:
            return prompt
        print("Промпт не найден, используется промпт из .env")
    elif choice == "3":
        prompt = input("Введите промпт: ")
        save_prompt(prompt)
        return prompt

    return os.getenv("SYSTEM_PROMPT", "Ты полезный ассистент.")


# Задание 2

settings = {"effort": "medium", "temperature": None}


# Задание 3

history = []


def get_response(text: str, client: OpenAI, system_prompt: str):
    messages = history + [{"role": "user", "content": text}]

    params = {
        "model": MODEL,
        "instructions": system_prompt,          # системный промпт
        "input": messages[-6:],                 # не больше 6 сообщений
        "reasoning": {"effort": settings["effort"]},
    }
    if settings["temperature"] is not None:
        params["temperature"] = settings["temperature"]

    response = client.responses.create(**params)

    history.append({"role": "user", "content": text})
    history.append({"role": "assistant", "content": response.output_text})
    del history[:-6]  # храним только 3 вопроса и 3 ответа

    return response


if __name__ == "__main__":
    system_prompt = choose_prompt()

    print("\nВведите ваш вопрос (или 'exit' для выхода)")
    print("Команды:")
    print("  /prompt           - сменить системный промпт")
    print("  /effort <уровень> - low, medium, high")
    print("  /temp <число>     - temperature, например /temp 0.7")
    print("  /clear            - очистить историю")

    while True:
        question = input("Вы: ")

        if question.lower() == "exit":
            print("Завершение программы.")
            break

        if question == "/prompt":
            system_prompt = choose_prompt()
            continue

        if question.startswith("/effort "):
            settings["effort"] = question.split()[1]
            print("effort =", settings["effort"])
            continue

        if question.startswith("/temp "):
            settings["temperature"] = float(question.split()[1])
            print("temperature =", settings["temperature"])
            continue

        if question == "/clear":
            history.clear()
            print("История очищена.")
            continue

        try:
            answer = get_response(question, client, system_prompt)
            print("AI:", answer.output_text)
        except Exception as e:
            print("Ошибка:", e)