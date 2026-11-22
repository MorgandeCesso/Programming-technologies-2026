from mistralai.client import Mistral
from dotenv import load_dotenv
from mistralai.client.models import TextChunk, ThinkChunk  # Импорт для парсинга рассуждений
import os
import sqlite3

load_dotenv(override=True)
api_key = os.getenv("MISTRAL_API_KEY")
client = Mistral(api_key=api_key)

MODEL = "mistral-small-2603"  # Сменили модель, так как ministral не поддерживает reasoning
MAX_HISTORY = 6  # 3 пары user + assistant


# ==================== БАЗА ДАННЫХ (SQLite) ====================
def init_db():
    """Создаёт базу и таблицу, если их ещё нет."""
    conn = sqlite3.connect("prompts.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            text TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def get_prompts_from_db() -> dict:
    """Достаёт все кастомные промпты из базы."""
    conn = sqlite3.connect("prompts.db")
    cur = conn.cursor()
    cur.execute("SELECT name, text FROM prompts")
    rows = cur.fetchall()
    conn.close()
    return {name: text for name, text in rows}  # {'my_prompt': '...'}


def add_prompt_to_db(name: str, text: str):
    """Сохраняет новый промпт в базу."""
    conn = sqlite3.connect("prompts.db")
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO prompts (name, text) VALUES (?, ?)", (name, text))
        conn.commit()
        print(f"Промпт '{name}' сохранён в базу!")
    except sqlite3.IntegrityError:
        print(f"Ошибка: промпт с именем '{name}' уже существует или не может быть создан!")
    finally:
        conn.close()


def delete_prompt_from_db(name: str):
    """Удаляет промпт из базы."""
    conn = sqlite3.connect("prompts.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM prompts WHERE name = ?", (name,))
    if cur.rowcount > 0:
        print(f"Промпт '{name}' удалён.")
    else:
        print(f"Промпта '{name}' нет в базе.")
    conn.commit()
    conn.close()


# ==================== ПРОМПТЫ ИЗ .ENV ====================
# В Mistral промпты достаём из переменных окружения
# с префиксом PROMPT_. В OpenAI это был бы параметр instructions.
def load_prompts_from_env() -> dict:
    """Собираем все переменные из .env, начинающиеся на PROMPT_."""
    prompts = {}
    for key, value in os.environ.items():
        if key.startswith("PROMPT_"):
            name = key[len("PROMPT_"):].lower()
            prompts[name] = value
    return prompts


# ==================== ГЛАВНОЕ МЕНЮ ====================
def pick_prompt(env_prompts: dict, db_prompts: dict) -> str:
    """Меню выбора/создания/удаления промптов."""
    while True:
        # Каждый раз объединяем актуальные данные из env и БД
        all_prompts = {**env_prompts, **db_prompts}

        print("\n--- МЕНЮ ПРОМПТОВ ---")
        print("1. Выбрать готовый промпт")
        print("2. Создать новый промпт (сохранится в БД)")
        print("3. Удалить промпт из БД")

        choice = input("Действие (1-3, Enter — выбрать default): ").strip()

        if choice == "1" or choice == "":
            if not all_prompts:
                print("Нет доступных промптов! Создайте новый.")
                continue
            print("\nДоступные промпты:", ", ".join(all_prompts.keys()))
            name = input("Какой выбрать (Enter — default): ").strip().lower()
            if name in all_prompts:
                return all_prompts[name]
            elif not name:
                return all_prompts.get("default", "Ты — полезный ассистент.")
            else:
                print("Такого промпта нет, попробуй снова.")

        elif choice == "2":
            name = input("Имя нового промпта (латиницей, без пробелов): ").strip().lower()
            if not name:
                print("Имя не может быть пустым.")
                continue
            text = input("Текст промпта: ").strip()
            add_prompt_to_db(name, text)
            # Обновляем локальный словарь, чтобы не перезапускать программу
            db_prompts.update(get_prompts_from_db())

        elif choice == "3":
            if not db_prompts:
                print("В базе пока нет промптов.")
                continue
            print("\nПромпты в базе:", ", ".join(db_prompts.keys()))
            name = input("Какой удалить: ").strip().lower()
            delete_prompt_from_db(name)
            # Перечитываем БД после удаления
            db_prompts = get_prompts_from_db()

        else:
            print("Не понял команду.")


def get_response(history: list, client: Mistral, temperature: float = 0.7):
    response = client.chat.complete(
        model=MODEL,
        messages=history,
        temperature=temperature,  # передаём температуру в API
        reasoning_effort="high"   # Включаем режим рассуждений
    )
    return response


# ==================== ЗАПУСК ====================
if __name__ == "__main__":
    init_db()  # создаём базу при старте

    # Загружаем промпты из двух источников
    env_prompts = load_prompts_from_env()
    db_prompts = get_prompts_from_db()

    # системный промпт задаётся через .env или БД,
    # в OpenAI это делалось бы через instructions="..."
    # Вызываем меню, передавая ему оба словаря
    system_prompt = pick_prompt(env_prompts, db_prompts)
    print(f"\nВыбран промпт: {system_prompt}\n")

    # История начинается с системного сообщения
    # ОТЛИЧИЕ: в Mistral роль "system" в messages — стандартный способ
    # задать поведение модели
    history = [{"role": "system", "content": system_prompt}]

    print("\n--- НАСТРОЙКИ МОДЕЛИ ---")
    temp_input = input("Введи temperature (от 0.0 до 1.5, Enter — 0.7): ").strip()
    try:
        temperature = float(temp_input) if temp_input else 0.7
    except ValueError:
        temperature = 0.7

    print(f"\nНастройки: model={MODEL}, temperature={temperature}\n")

    print("Введите ваш вопрос (или 'exit' для выхода):")

    while True:
        question = input("Вы: ")
        if question.lower() == "exit":
            print("Завершение программы.")
            break

        # Добавляем реплику пользователя в историю
        history.append({"role": "user", "content": question})

        # Обрезаем историю до 6 последних сообщений
        if len(history) > MAX_HISTORY + 1:  # +1 — это system-сообщение
            history = [history[0]] + history[-MAX_HISTORY:]

        # Отправляем ВСЮ историю а не только текущий вопрос
        answer = get_response(history, client, temperature=temperature)

        # ==================== ПАРСИНГ РАССУЖДЕНИЙ И ОТВЕТА ====================
        content = answer.choices[0].message.content
        answer_text = ""

        print("\n--- РАССУЖДЕНИЯ МОДЕЛИ ---")
        if isinstance(content, list):
            for chunk in content:
                if isinstance(chunk, ThinkChunk):
                    for inner in chunk.thinking:
                        print(inner.text, end="", flush=True)
                elif isinstance(chunk, TextChunk):
                    print("\n\n--- ФИНАЛЬНЫЙ ОТВЕТ ---")
                    print(chunk.text)
                    answer_text = chunk.text
        else:
            # Если модель не вернула рассуждения (или reasoning_effort не сработал)
            print(content)
            answer_text = content

        # ВЫВОД JSON-ФАЙЛА (как просил препод)
        print("\n--- СЫРОЙ JSON ОТВЕТА ---")
        print(answer.model_dump_json(indent=2))

        # Добавляем ответ ассистента в историю
        # ВАЖНО: передаём полный content (с рассуждениями), чтобы модель не теряла контекст
        history.append({"role": "assistant", "content": content})