import os
from pathlib import Path
from time import perf_counter

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError


load_dotenv(Path(__file__).resolve().parent / ".env", override=True)


def main():
    api_key = os.getenv("LMSTUDIO_API_KEY")

    if not api_key:
        print("укажи LMSTUDIO_API_KEY в файле .env.")
        return

    client = OpenAI(
        base_url=os.getenv(
            "LMSTUDIO_BASE_URL",
            "http://127.0.0.1:1234/v1",
        ),
        api_key=api_key,
        timeout=180.0,
        max_retries=0,
    )

    model_name = os.getenv(
        "LMSTUDIO_MODEL",
        "qwen2.5-1.5b-instruct",
    )

    try:
        print("модели на локальном сервере:")
        for model in client.models.list().data:
            print(f"  - {model.id}")

        question = (
            "ответь на русском языке одним предложением: "
            "что такое переменная в программировании?"
        )

        print(f"\nвыбранная модель: {model_name}")
        print(f"вопрос: {question}")
        print("ожидаем ответ...")

        start = perf_counter()

        response = client.responses.create(
            model=model_name,
            input=question,
            temperature=0.2,
            max_output_tokens=256,
        )

        elapsed = perf_counter() - start

        print("\nответ:", response.output_text)
        print(f"время получения полного ответа: {elapsed:.2f} с")
        print(f"статус: {response.status}")

    except OpenAIError as error:
        print(f"ошибка API ({type(error).__name__}): {error}")


if __name__ == "__main__":
    main()
    