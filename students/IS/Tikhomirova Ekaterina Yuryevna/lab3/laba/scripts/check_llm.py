from openai import APIConnectionError, APIStatusError, APITimeoutError

from app.clients.llm import generate_text


def main():
    instructions = (
        "отвечай по-русски, кратко, только по приведенному контексту. "
        "если ответа в контексте нет, сообщи об этом. "
        "не добавляй неподтвержденные сведения."
    )

    prompt = """
контекст:
измерение считается устаревшим, если с момента последнего
полученного измерения прошло более 60 секунд.
равно 60 секунд еще не считается превышением.

вопрос:
когда измерение считается устаревшим?
""".strip()

    print("ожидаем ответ Qwen...")
    answer = generate_text(instructions, prompt)

    print("\nответ:")
    print(answer)


if __name__ == "__main__":
    try:
        main()
    except APITimeoutError:
        print("превышено время ожидания ответа модели")
    except APIConnectionError:
        print("не удалось подключиться к LM Studio")
    except APIStatusError as error:
        print("ошибка HTTP:", error.status_code)
    except ValueError as error:
        print("ошибка:", error)