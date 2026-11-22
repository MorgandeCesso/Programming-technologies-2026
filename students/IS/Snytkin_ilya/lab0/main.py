import argparse
import os
import sqlite3
from contextlib import closing
from pathlib import Path
from time import perf_counter

from dotenv import load_dotenv
from openai import APIError, OpenAI

PROJECT_DIR = Path(__file__).resolve().parent


def get_answer(client, provider, model, prompt, messages, effort, temperature):
    if provider == "local":
        response = client.responses.create(
            model=model,
            instructions=prompt,
            input=[{"type": "message", **message} for message in messages],
            temperature=temperature,
            reasoning={"effort": "medium" if effort == "on" else "none"},
            max_output_tokens=1024,
        )
        return response.output_text

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": prompt}] + messages,
        temperature=temperature,
        reasoning_effort=effort,
    )
    return response.choices[0].message.content if response.choices else ""


def chat(client, db, provider, model, default_prompt):
    prompt = default_prompt
    history = []
    temperature = 1.0
    if provider == "local":
        levels, effort = ("none", "on"), "none"
    else:
        levels, effort = ("minimal", "low", "medium", "high"), "medium"

    print(f"{provider}: {model}. effort={effort}, temperature={temperature}")
    print("/save — сохранить и включить промпт, /prompt — список, /prompt ID — выбрать")
    print(f"/effort {'|'.join(levels)}, /temperature 0–2, /clear, exit")

    while True:
        question = input("Вы: ").strip()
        if not question:
            continue
        if question.lower() == "exit":
            break

        command, _, value = question.partition(" ")
        value = value.strip()
        if command == "/save":
            name = input("Название: ").strip()
            text = input("Системный промпт: ").strip()
            if not name or not text:
                print("Введите название и текст промпта.")
                continue
            with db:
                db.execute("INSERT INTO prompts (name, text) VALUES (?, ?)", (name, text))
            prompt = text
            print(f"Сохранён и включён промпт «{name}».")
        elif command == "/prompt" and not value:
            print("0 — промпт из .env")
            for number, name in db.execute("SELECT id, name FROM prompts ORDER BY id"):
                print(f"{number} — {name}")
        elif command == "/prompt" and value == "0":
            prompt = default_prompt
            print("Включён промпт из .env.")
        elif command == "/prompt":
            saved = db.execute("SELECT name, text FROM prompts WHERE id = ?", (value,)).fetchone()
            if saved:
                name, prompt = saved
                print(f"Включён промпт «{name}».")
            else:
                print("Промпт с таким ID не найден.")
        elif command == "/effort":
            if value in levels:
                effort = value
                print(f"Уровень рассуждения: {effort}.")
            else:
                print("Доступные уровни:", ", ".join(levels))
        elif command == "/temperature":
            try:
                value = float(value.replace(",", "."))
            except ValueError:
                print("Введите температуру от 0 до 2.")
                continue
            if 0 <= value <= 2:
                temperature = value
                print(f"temperature = {temperature}")
            else:
                print("Введите температуру от 0 до 2.")
        elif command == "/clear":
            history.clear()
            print("История очищена.")
        elif question.startswith("/"):
            print("Неизвестная команда.")
        else:
            messages = history[-4:] + [{"role": "user", "content": question}]
            started = perf_counter()
            try:
                answer = get_answer(client, provider, model, prompt, messages, effort, temperature)
            except APIError as error:
                print(f"Ошибка API ({type(error).__name__}).")
                continue
            if answer:
                print("AI:", answer)
                print(f"Время запроса: {perf_counter() - started:.2f} с.")
                history = messages + [{"role": "assistant", "content": answer}]
            else:
                print("API не вернул текст ответа.")


def main():
    parser = argparse.ArgumentParser(description="Консольный чат-бот")
    parser.add_argument("provider", choices=["gemini", "local"], nargs="?", default="gemini")
    provider = parser.parse_args().provider

    load_dotenv(PROJECT_DIR / ".env")
    prompt = os.getenv("SYSTEM_PROMPT") or "Отвечай кратко на русском языке."
    if provider == "local":
        model = "qwen3-0.6b"
        client = OpenAI(base_url="http://127.0.0.1:8080/v1", api_key="local", timeout=180)
    else:
        key = os.getenv("GEMINI_API_KEY", "").strip()
        if not key:
            print("Укажите GEMINI_API_KEY в .env.")
            return 1
        model = os.getenv("GEMINI_MODEL", "").strip() or "gemini-3.1-flash-lite"
        client = OpenAI(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=key,
        )

    with client, closing(sqlite3.connect(PROJECT_DIR / "prompts.db")) as db:
        db.execute("CREATE TABLE IF NOT EXISTS prompts (id INTEGER PRIMARY KEY, name TEXT, text TEXT)")
        try:
            chat(client, db, provider, model, prompt)
        except (EOFError, KeyboardInterrupt):
            print("\nЗавершение программы.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
