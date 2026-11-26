import sys

import httpx
from openai import APIConnectionError, APIStatusError, APITimeoutError

from app.logic.crag import ask_crag


def main():
    question = " ".join(sys.argv[1:]).strip()

    if not question:
        question = "когда измерение считается устаревшим?"

    print("вопрос:", question)
    print("выполняем поиск, оценку фрагментов и подготовку ответа...")

    result = ask_crag(question)

    print("\nответ:")
    print(result["answer"])

    print("\nоценки найденных фрагментов:")

    for source in result["sources"]:
        print(
            f"\n[{source['id']}] {source['source']}, "
            f"чанк {source['chunk']}"
        )
        print("сходство:", round(source["score"], 4))
        print("оценка:", source["grade"])
        print("обоснование:", source["reason"])
        print("цитата:", source["evidence"])
        print(
            "использован для ответа:",
            "да" if source["used"] else "нет",
        )


if __name__ == "__main__":
    try:
        main()
    except (APITimeoutError, httpx.TimeoutException):
        print("превышено время ожидания модели")
        sys.exit(1)
    except (APIConnectionError, httpx.RequestError):
        print("не удалось подключиться к LM Studio")
        sys.exit(1)
    except APIStatusError as error:
        print("ошибка модели, HTTP:", error.status_code)
        sys.exit(1)
    except httpx.HTTPStatusError as error:
        print("ошибка эмбеддингов, HTTP:", error.response.status_code)
        sys.exit(1)
    except ValueError as error:
        print("ошибка проверки:", error)
        sys.exit(1)