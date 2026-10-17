import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError


env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path, override=True)


def main():
    api_key = os.getenv("ZAI_API_KEY")

    if not api_key or not api_key.strip():
        print("Укажи ZAI_API_KEY в файле .env.")
        return

    model = os.getenv("ZAI_MODEL", "glm-4.5-flash")

    prompts = {
        "default": os.getenv(
            "SYSTEM_PROMPT",
            "Отвечай на русском языке кратко и понятно.",
        ),
        "teacher": os.getenv(
            "PROMPT_TEACHER",
            "Объясняй на русском языке как преподаватель для начинающего.",
        ),
        "expert": os.getenv(
            "PROMPT_EXPERT",
            "Отвечай на русском языке как технический эксперт.",
        ),
    }

    active_prompt = "default"
    temperature = 0.7
    history = []

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.z.ai/api/paas/v4/",
        timeout=90.0,
        max_retries=0,
    )

    print("Чат-бот Z.AI запущен.")
    print(f"Модель: {model}")
    print("Команды:")
    print("/prompt default | /prompt teacher | /prompt expert")
    print("/temp число — температура от 0 до 1, например /temp 0.2")
    print("/clear — очистить историю")
    print("/history — показать историю")
    print("/settings — показать настройки")
    print("exit — выход")

    while True:
        question = input("\nВы: ").strip()

        if not question:
            continue

        if question.lower() == "exit":
            print("Завершение программы.")
            break

        if question == "/settings":
            print(f"Модель: {model}")
            print(f"Промпт: {active_prompt}")
            print(f"Инструкция: {prompts[active_prompt]}")
            print(f"Температура: {temperature}")
            print(f"Сообщений в истории: {len(history)}/6")
            continue

        if question.startswith("/prompt "):
            name = question.removeprefix("/prompt ").strip()

            if name in prompts:
                active_prompt = name
                print(f"Промпт переключён: {name}")
            else:
                print("Доступные промпты:", ", ".join(prompts))
            continue

        if question.startswith("/temp "):
            try:
                value = float(question.split(maxsplit=1)[1].replace(",", "."))
                if not 0 <= value <= 1:
                    raise ValueError
                temperature = value
                print(f"Температура: {temperature}")
            except ValueError:
                print("Введи число от 0 до 1, например /temp 0.2")
            continue

        if question == "/clear":
            history.clear()
            print("История очищена.")
            continue

        if question == "/history":
            if not history:
                print("История пуста.")
            for number, message in enumerate(history, start=1):
                print(f"{number}. {message['role']}: {message['content']}")
            print(f"Сообщений: {len(history)}/6")
            continue

        if question.startswith("/"):
            print("Неизвестная команда.")
            continue

        recent_messages = history[-4:] + [
            {"role": "user", "content": question}
        ]

        try:
            print("Ожидаем ответ...")

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompts[active_prompt]},
                    *recent_messages,
                ],
                temperature=temperature,
                max_tokens=700,
                extra_body={"thinking": {"type": "disabled"}},
            )

            answer = response.choices[0].message.content

            if not answer:
                print("Получен пустой ответ. История не изменена.")
                continue

            print("AI:", answer)

            history = recent_messages + [
                {"role": "assistant", "content": answer}
            ]

            if response.choices[0].finish_reason == "length":
                print("[Ответ обрезан из-за ограничения длины.]")

        except OpenAIError as error:
            print(f"Ошибка API ({type(error).__name__}): {error}")


if __name__ == "__main__":
    main()
