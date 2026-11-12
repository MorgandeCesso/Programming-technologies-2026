import os
import json
import sqlite3
import time
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI, APIError

load_dotenv()

DB_PATH = "prompts.db"
HISTORY_LIMIT = 6
EFFORTS = ("none", "low", "medium", "high")
RESULTS_DIR = "results"

# ---------- Профили бэкендов ----------
PROFILES = {
    "remote": dict(
        base_url=os.getenv("OPENAI_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("MODEL", "gpt-6-luna"),
        reasoning=True,
    ),
    "local": dict(
        base_url=os.getenv("LOCAL_BASE_URL", "http://localhost:7000/v1"),
        api_key=os.getenv("LOCAL_API_KEY", "lm-studio"),
        model=os.getenv("LOCAL_MODEL", ""),
        reasoning=False,
    ),
}


def make_client(profile: dict) -> OpenAI:
    return OpenAI(base_url=profile["base_url"], api_key=profile["api_key"])


# ---------- Тестовые запросы для лабы №1 ----------
CODE_WITH_BUG = """def average(numbers):
    total = 0
    for n in numbers:
        total += n
    return total / len(numbers) + 1
"""

TEXT = ("Компания «Альфа» основана в 2015 году в Красноярске Иваном Петровым. "
        "В 2020 году штат вырос до 120 сотрудников, а выручка составила 50 млн рублей. "
        "Основной продукт компании — приложение для учёта склада.")

TESTS = [
    dict(name="Объяснение понятия",
         instructions="Отвечай кратко, простым языком, на русском.",
         input="Объясни, что такое рекурсия в программировании."),
    dict(name="Функция на Python",
         instructions="Верни только код на Python без пояснений.",
         input="Напиши функцию is_palindrome(s), которая проверяет, является ли строка палиндромом, игнорируя регистр и пробелы."),
    dict(name="Поиск ошибки в коде",
         instructions="Найди ошибку, объясни её и приведи исправленный код.",
         input=f"В этой функции должно считаться среднее арифметическое. Найди ошибку:\n{CODE_WITH_BUG}"),
    dict(name="Извлечение в JSON",
         instructions="Верни ТОЛЬКО валидный JSON без пояснений и markdown.",
         input=f"Извлеки из текста поля: company, founded_year, city, founder, employees, revenue_mln_rub.\n\nТекст: {TEXT}"),
    dict(name="Вопрос без ответа в тексте",
         instructions="Отвечай только по предоставленному тексту. Если информации недостаточно, сообщи об этом.",
         input=f"Текст: {TEXT}\n\nВопрос: Сколько офисов у компании «Альфа» за границей?"),
]


# ---------- База промптов (задание из лабы №0) ----------
def init_db():
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            text TEXT NOT NULL)""")


def save_prompt(name, text):
    with sqlite3.connect(DB_PATH) as con:
        con.execute("INSERT OR REPLACE INTO prompts (name, text) VALUES (?, ?)", (name, text))


def list_prompts():
    with sqlite3.connect(DB_PATH) as con:
        return con.execute("SELECT id, name, text FROM prompts").fetchall()


def choose_prompt(current):
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


# ---------- Запрос к модели ----------
def get_response(client, profile, input_, instructions=None, effort=None,
                 temperature=None, max_output_tokens=None):
    params = {"model": profile["model"], "input": input_}
    if profile["reasoning"] and effort:
        params["reasoning"] = {"effort": effort}
    if instructions:
        params["instructions"] = instructions
    if temperature is not None:
        params["temperature"] = temperature
    if max_output_tokens:
        params["max_output_tokens"] = max_output_tokens
    return client.responses.create(**params)


def usage_info(resp):
    """Безопасно достаёт статистику токенов (у разных серверов поля разные)."""
    u = getattr(resp, "usage", None)
    if not u:
        return {}
    details = getattr(u, "output_tokens_details", None)
    return {
        "output_tokens": getattr(u, "output_tokens", None),
        "reasoning_tokens": getattr(details, "reasoning_tokens", None) if details else None,
    }


def save_results(filename, data):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    path = os.path.join(RESULTS_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Сохранено:", path)


def safe_name(model: str) -> str:
    return model.replace("/", "_").replace(":", "_")


# ---------- Бенчмарк (лаба №1, пункты 3-4, 6) ----------
def run_bench(client, profile, temperature, max_tokens):
    results = []
    for i, t in enumerate(TESTS, 1):
        print(f"\n=== Тест {i}: {t['name']} ===")
        start = time.perf_counter()
        try:
            resp = get_response(client, profile, t["input"], t["instructions"],
                                temperature=temperature, max_output_tokens=max_tokens)
            text = resp.output_text
            info = usage_info(resp)
        except APIError as e:
            text, info = f"ОШИБКА: {e}", {}
        elapsed = time.perf_counter() - start
        print(text)
        print(f"[{elapsed:.1f} с, {info}]")
        results.append(dict(test=i, name=t["name"], seconds=round(elapsed, 2),
                            usage=info, answer=text))
    stamp = datetime.now().strftime("%H%M%S")
    save_results(f"bench_{safe_name(profile['model'])}_{stamp}.json", dict(
        model=profile["model"], temperature=temperature,
        max_output_tokens=max_tokens, results=results))


# ---------- Эксперимент с температурой (пункт 5) ----------
def run_temp_experiment(client, profile, test_no, max_tokens):
    t = TESTS[test_no - 1]
    out = []
    for temp in (0.2, 1.0):
        for run in range(1, 4):
            print(f"\n--- temperature={temp}, запуск {run}/3 ---")
            start = time.perf_counter()
            try:
                resp = get_response(client, profile, t["input"], t["instructions"],
                                    temperature=temp, max_output_tokens=max_tokens)
                text = resp.output_text
            except APIError as e:
                text = f"ОШИБКА: {e}"
            elapsed = time.perf_counter() - start
            print(text)
            print(f"[{elapsed:.1f} с]")
            out.append(dict(temperature=temp, run=run, seconds=round(elapsed, 2), answer=text))
    stamp = datetime.now().strftime("%H%M%S")
    save_results(f"temp_{safe_name(profile['model'])}_{stamp}.json",
                 dict(model=profile["model"], test=t["name"], runs=out))


HELP = """Команды:
  /backend local|remote - переключить сервер (LM Studio / Groq)
  /models               - список моделей на текущем сервере
  /model X              - сменить модель
  /bench                - прогнать 5 тестовых запросов
  /tempexp N            - тест N (1-5) по 3 раза при temp 0.2 и 1.0
  /prompt, /newprompt   - системные промпты
  /effort X             - none | low | medium | high (только remote)
  /temp X               - temperature (/temp off - сбросить)
  /maxtokens N          - лимит токенов ответа (для тестов)
  /history, /clear      - история
  exit                  - выход"""

if __name__ == "__main__":
    init_db()
    backend = os.getenv("BACKEND", "remote")
    profile = PROFILES[backend]
    client = make_client(profile)
    system_prompt = os.getenv("SYSTEM_PROMPT")
    effort, temperature, max_tokens = "medium", None, 1500
    history = []
    print(HELP)
    print(f"Бэкенд: {backend}, модель: {profile['model']}")

    while True:
        q = input("Вы: ").strip()
        if not q:
            continue
        if q.lower() == "exit":
            print("Завершение программы.")
            break

        if q.startswith("/backend"):
            parts = q.split()
            if len(parts) != 2 or parts[1] not in PROFILES:
                print("Использование: /backend local | remote")
                continue
            backend = parts[1]
            profile = PROFILES[backend]
            client = make_client(profile)
            history.clear()
            print(f"Бэкенд: {backend}, модель: {profile['model']}")
            continue
        if q == "/models":
            try:
                for m in client.models.list().data:
                    print("  -", m.id)
            except APIError as e:
                print("Ошибка API:", e)
            continue
        if q.startswith("/model"):
            parts = q.split(maxsplit=1)
            if len(parts) == 2:
                profile["model"] = parts[1].strip()
                print("Модель:", profile["model"])
            else:
                print("Использование: /model имя_модели")
            continue
        if q == "/bench":
            run_bench(client, profile, temperature if temperature is not None else 0.2, max_tokens)
            continue
        if q.startswith("/tempexp"):
            parts = q.split()
            if len(parts) == 2 and parts[1].isdigit() and 1 <= int(parts[1]) <= len(TESTS):
                run_temp_experiment(client, profile, int(parts[1]), max_tokens)
            else:
                print(f"Использование: /tempexp 1..{len(TESTS)}")
            continue
        if q.startswith("/maxtokens"):
            parts = q.split()
            if len(parts) == 2 and parts[1].isdigit():
                max_tokens = int(parts[1])
                print("max_output_tokens =", max_tokens)
            else:
                print("Использование: /maxtokens 1500")
            continue

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
            if len(parts) == 2 and parts[1] == "off":
                temperature = None
                print("temperature сброшена")
                continue
            try:
                temperature = float(parts[1])
            except (IndexError, ValueError):
                print("Использование: /temp 0.7 или /temp off")
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
            resp = get_response(client, profile, history[-HISTORY_LIMIT:],
                                system_prompt, effort, temperature)
        except APIError as e:
            print("Ошибка API:", e)
            history.pop()
            continue
        elapsed = time.perf_counter() - start
        print("AI:", resp.output_text)
        print(f"[{elapsed:.1f} с, {usage_info(resp)}]")
        history.append({"role": "assistant", "content": resp.output_text})