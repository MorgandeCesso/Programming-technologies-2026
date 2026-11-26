import sys

import httpx
from openai import APIConnectionError, APIStatusError, APITimeoutError

from app.logic.rag import ask_rag


def main():
    question = " ".join(sys.argv[1:]).strip()

    if not question:
        question = "когда измерение считается устаревшим?"

    print("вопрос:", question)
    print("выполняем поиск и формируем ответ...")

    result = ask_rag(question)

    print("\nответ:")
    print(result["answer"])

    print("\nнайденные источники:")

    for source in result["sources"]:
        print(
            f"[{source['id']}] {source['source']}, "
            f"чанк {source['chunk']}, "
            f"сходство {source['score']:.4f}"
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
        print("ошибка:", error)
        sys.exit(1)