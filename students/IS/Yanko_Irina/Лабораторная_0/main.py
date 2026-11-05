
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
BASE_URL = os.getenv(
    "BASE_URL",
    "https://openrouter.ai/api/v1"
).strip()
MODEL = os.getenv("MODEL", "openrouter/free").strip()

SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "Ты полезный русскоязычный ассистент. "
    "Отвечай понятно, корректно и по существу."
)

REASONING_EFFORT = os.getenv(
    "REASONING_EFFORT",
    "medium"
).strip().lower()

TEMPERATURE = float(os.getenv("TEMPERATURE", "1.0"))

VALID_REASONING_LEVELS = {
    "none",
    "low",
    "medium",
    "high"
}


def load_system_prompt() -> str:
    load_dotenv(override=True)

    return os.getenv(
        "SYSTEM_PROMPT",
        "Ты полезный русскоязычный ассистент."
    ).strip()


def get_response(
    client: OpenAI,
    user_text: str,
    history: list[dict[str, str]],
    system_prompt: str,
    reasoning_effort: str,
    temperature: float
) -> str:

    current_history = history[-6:]

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        *current_history,
        {
            "role": "user",
            "content": user_text
        }
    ]

    request_options = {
        "model": MODEL,
        "messages": messages
    }

    if reasoning_effort == "none":
        request_options["temperature"] = temperature
    else:
        request_options["extra_body"] = {
            "reasoning": {
                "effort": reasoning_effort
            }
        }

    try:
        response = client.chat.completions.create(
            **request_options
        )

        answer = response.choices[0].message.content or ""
        answer = answer.strip()

        if not answer:
            answer = "Модель не вернула текстовый ответ."

    except Exception as error:
        print(f"\nОшибка при обращении к API: {error}")
        return ""

    history.append({
        "role": "user",
        "content": user_text
    })

    history.append({
        "role": "assistant",
        "content": answer
    })

    # Оставляем максимум шесть сообщений
    del history[:-6]

    return answer


def print_help() -> None:
    print(
        "\nКоманды:\n"
        "  /help       — список команд\n"
        "  /clear      — очистить историю диалога\n"
        "  /prompt     — перечитать системный промпт из .env\n"
        "  /reasoning  — изменить уровень рассуждения\n"
        "  /temperature — изменить температуру\n"
        "  /exit       — завершить программу\n"
    )


def main() -> None:

    if not API_KEY:
        print(
            "Ошибка: не найден OPENROUTER_API_KEY.\n"
            "Добавь свой ключ в файл .env."
        )
        print("Получить ключ: https://openrouter.ai/keys")
        return

    if REASONING_EFFORT not in VALID_REASONING_LEVELS:
        print(
            "Ошибка: REASONING_EFFORT должен быть одним из значений: "
            "none, low, medium, high."
        )
        return

    if not 0 <= TEMPERATURE <= 2:
        print("Ошибка: TEMPERATURE должна быть от 0 до 2.")
        return
    client = OpenAI(
        api_key=API_KEY,
        base_url=BASE_URL
    )

    history: list[dict[str, str]] = []

    current_reasoning = REASONING_EFFORT
    current_temperature = TEMPERATURE
    current_prompt = load_system_prompt()

    print("=" * 50)
    print("Учебный чат-бот — OpenRouter API")
    print("=" * 50)
    print(f"Модель: {MODEL}")
    print(f"Уровень рассуждения: {current_reasoning}")
    print(f"Температура: {current_temperature}")
    print("История: последние 6 сообщений")
    print_help()

    while True:
        try:
            user_text = input("\nТы: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nРабота чат-бота завершена.")
            break

        if not user_text:
            continue

        command = user_text.lower()

        if command in ("/exit", "/quit", "выход"):
            print("Работа чат-бота завершена.")
            break

        elif command == "/help":
            print_help()
            continue

        elif command == "/clear":
            history.clear()
            print("История диалога очищена.")
            continue

        elif command == "/prompt":
            current_prompt = load_system_prompt()
            print("Системный промпт перечитан из .env.")
            continue

        elif command == "/reasoning":
            print(
                "Выбери уровень рассуждения: "
                "none, low, medium, high"
            )
            new_level = input("Уровень: ").strip().lower()

            if new_level not in VALID_REASONING_LEVELS:
                print("Неизвестный уровень.")
            else:
                current_reasoning = new_level
                print(
                    f"Уровень рассуждения изменён: "
                    f"{current_reasoning}"
                )
            continue

        elif command == "/temperature":
            new_value = input(
                "Введи температуру от 0 до 2: "
            ).strip()

            try:
                value = float(new_value)

                if not 0 <= value <= 2:
                    print("Значение должно быть от 0 до 2.")
                else:
                    current_temperature = value
                    print(
                        f"Температура изменена: "
                        f"{current_temperature}"
                    )

            except ValueError:
                print("Ошибка: нужно ввести число.")

            continue

        print("\nАссистент: ", end="", flush=True)

        answer = get_response(
            client=client,
            user_text=user_text,
            history=history,
            system_prompt=current_prompt,
            reasoning_effort=current_reasoning,
            temperature=current_temperature
        )

        if answer:
            print(answer)


if __name__ == "__main__":
    main()
