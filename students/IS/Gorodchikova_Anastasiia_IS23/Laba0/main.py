from openai import OpenAI
from dotenv import load_dotenv
import os
import sqlite3

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
system_prompt = os.getenv("SYSTEM_PROMPT")

client = OpenAI(api_key=api_key , base_url="https://api.groq.com/openai/v1")

conn = sqlite3.connect("prompts.db")
conn.execute("CREATE TABLE IF NOT EXISTS prompts (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, text TEXT)")
conn.commit()

def save_prompt(name, text):
    conn.execute("INSERT INTO prompts (name, text) VALUES (?, ?)", (name, text))
    conn.commit()

def get_prompts():
    return conn.execute("SELECT id, name, text FROM prompts").fetchall()

def choose_prompt():
    print("\nВыберите системный промпт:")
    print("1 - из .env")
    print("2 - из базы данных")
    print("3 - ввести новый (сохранится в базу)")
    choice = input("> ")

    if choice == "1":
        return os.getenv("SYSTEM_PROMPT")

    if choice == "2":
        prompts = get_prompts()
        if not prompts:
            print("В базе пока пусто, используем промпт из .env")
            return os.getenv("SYSTEM_PROMPT")
        for p in prompts:
            print(p[0], "-", p[1], ":", p[2])
        num = input("Номер промпта: ")
        for p in prompts:
            if str(p[0]) == num:
                return p[2]
        print("Нет такого номера, используем промпт из .env")
        return os.getenv("SYSTEM_PROMPT")

    if choice == "3":
        name = input("Название: ")
        text = input("Текст промпта: ")
        save_prompt(name, text)
        return text

    print("Непонятный выбор, используем промпт из .env")
    return os.getenv("SYSTEM_PROMPT")

def get_response(text: str, client: OpenAI):
    response = client.responses.create(model="qwen/qwen3.8-27b", input=text, instructions=system_prompt, reasoning={"effort": "none"}, temperature=1, max_output_tokens=800)
    return response

if __name__ == "__main__":
    system_prompt = choose_prompt()
    print("Введите ваш вопрос (или 'exit' для выхода):")
    history = []
    while True:
        question = input("Вы: ")
        if question.lower() == "exit":
            print("Завершение программы.")
            break
        if question == "/prompt":
            system_prompt = choose_prompt()
            print("Системный промпт сменён!")
            continue
        history.append({"role": "user", "content": question})
        history = history[-6:]
        answer = get_response(history, client)
        print("AI:", answer.output_text)
        print("[статус:", answer.status, "| причина:", answer.incomplete_details, "]")
        history.append({"role": "assistant", "content": answer.output_text})