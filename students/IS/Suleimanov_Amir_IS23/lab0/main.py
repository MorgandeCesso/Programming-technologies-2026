import os
import sqlite3
import time
from dotenv import load_dotenv
from openai import OpenAI, APIError

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("MODEL", "gpt-6-luna")
DB_PATH = "prompts.db"
HISTORY_LIMIT = 6  # 3 реплики пользователя + 3 ассистента
EFFORTS = ("none", "low", "medium", "high")


# ---------- База промптов (задание 1) ----------
def init_db():
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            text TEXT NOT NULL)""")


def save_prompt(name: str, text: str):
    with sqlite3.connect(DB_PATH) as con:
        con.execute("INSERT OR REPLACE INTO prompts (name, text) VALUES (?, ?)", (name, text))


def list_prompts():
    with sqlite3.connect(DB_PATH) as con:
        return con.execute("SELECT id, name, text FROM prompts").fetchall()


def choose_prompt(current: str | None) -> str | None:
    prompts = list_prompts()
    print("0. Из .env (SYSTEM_PROMPT)")
    for pid, name, text in prompts:
        print(f"{pid}. {name}: {text[:60]}")
    choice = input("Номер промпта: ").strip()
    if choice == "0":
        return os.getenv("SYSTEM_PROMPT")
    for pid, _, text in prompts:
        if str(pid) == choice:
            return text
    print("Не найден, оставляю текущий.")
    return current


# ---------- Запрос к API (задания 2 и 3) ----------
def get_response(history, instructions, effort, temperature):
    params = {
        "model": MODEL,
        "input": history[-HISTORY_LIMIT:],   # только последние 6 сообщений
        "reasoning": {"effort": effort},
    }
    if instructions:
        params["instructions"] = instructions
    # OpenAI принимает temperature только при effort=none, Groq - при любом effort
    if temperature is not None:
        params["temperature"] = temperature
    return client.responses.create(**params)


HELP = """Команды:
  /prompt        - выбрать системный промпт (хотсвап)
  /newprompt     - создать промпт и сохранить в БД
  /effort X      - none | low | medium | high
  /temp X        - temperature от 0 до 2
  /history       - показать историю
  /clear         - очистить историю
  exit           - выход"""

if __name__ == "__main__":
    init_db()
    system_prompt = os.getenv("SYSTEM_PROMPT")
    effort, temperature = "medium", None
    history = []
    print(HELP)

    while True:
        q = input("Вы: ").strip()
        if not q:
            continue
        if q.lower() == "exit":
            print("Завершение программы.")
            break
        if q == "/prompt":
            system_prompt = choose_prompt(system_prompt)
            print("Текущий промпт:", system_prompt)
            continue
        if q == "/newprompt":
            name = input("Название: ").strip()
            text = input("Текст промпта: ").strip()
            save_prompt(name, text)
            system_prompt = text
            print("Сохранено и активировано.")
            continue
        if q.startswith("/effort"):
            parts = q.split()
            if len(parts) != 2 or parts[1] not in EFFORTS:
                print("Использование: /effort none | low | medium | high")
                continue
            effort = parts[1]
            print("effort =", effort)
            continue
        if q.startswith("/temp"):
            parts = q.split()
            try:
                temperature = float(parts[1])
            except (IndexError, ValueError):
                print("Использование: /temp 0.7")
                continue
            print("temperature =", temperature)
            continue
        if q == "/history":
            for m in history[-HISTORY_LIMIT:]:
                print(f"[{m['role']}] {m['content']}")
            continue
        if q == "/clear":
            history.clear()
            print("История очищена.")
            continue

        history.append({"role": "user", "content": q})
        start = time.perf_counter()
        try:
            resp = get_response(history, system_prompt, effort, temperature)
        except APIError as e:
            print("Ошибка API:", e)
            history.pop()
            continue
        elapsed = time.perf_counter() - start
        print("AI:", resp.output_text)
        if resp.usage:
            reasoning = resp.usage.output_tokens_details.reasoning_tokens
            print(f"[{elapsed:.1f} с, reasoning-токенов: {reasoning}, "
                  f"всего на выходе: {resp.usage.output_tokens}]")
        history.append({"role": "assistant", "content": resp.output_text})