import sys

import httpx
from openai import APIConnectionError, APIStatusError, APITimeoutError

from app.logic.grading import grade_fragment
from app.logic.retrieval import search


def main():
    question = " ".join(sys.argv[1:]).strip()

    if not question:
        question = (
            "если с последнего измерения прошло ровно 60 секунд, "
            "считается ли оно устаревшим?"
        )

    print("вопрос:", question)
    print("ищем первый фрагмент...")

    hits = search(question, limit=1)

    if not hits:
        raise ValueError("фрагменты не найдены")

    hit = hits[0]

    print("источник:", hit["source"])
    print("оцениваем пригодность фрагмента...")

    result = grade_fragment(question, hit["text"])

    print("\nпроверенный JSON:")
    print(result.model_dump_json(indent=2))


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