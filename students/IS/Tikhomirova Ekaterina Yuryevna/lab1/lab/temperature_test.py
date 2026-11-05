import json
import os
from datetime import datetime
from time import perf_counter

from openai import OpenAI, OpenAIError

from experiment import ROOT, SYSTEM_PROMPT


PROMPT = (
    "придумай три разных названия приложения для планирования учебы. "
    "для каждого добавь пояснение не длиннее пяти слов. "
    "ответь на русском языке ровно тремя пронумерованными пунктами. "
    "не добавляй вступление и заключение."
)


def main():
    api_key = os.getenv("LMSTUDIO_API_KEY")

    if not api_key:
        print("укажи LMSTUDIO_API_KEY в .env.")
        return

    model = os.getenv("LMSTUDIO_MODEL", "qwen2.5-1.5b-instruct")

    client = OpenAI(
        api_key=api_key,
        base_url=os.getenv(
            "LMSTUDIO_BASE_URL",
            "http://127.0.0.1:1234/v1",
        ),
        timeout=180.0,
        max_retries=0,
    )

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output_dir = ROOT / "results" / f"temperature_{run_id}"
    output_dir.mkdir(parents=True)

    print(f"модель: {model}")
    print(f"запрос: {PROMPT}")
    print(f"папка результатов: {output_dir}")

    print("\nПрогрев модели...")
    try:
        client.responses.create(
            model=model,
            input="ответь одним словом: привет.",
            temperature=0.2,
            max_output_tokens=32,
        )
    except OpenAIError as error:
        print("ошибка прогрева:", error)
        return

    for repeat in range(1, 4):
        for temperature in (0.2, 1.0):
            print(f"\nтемпература: {temperature}, попытка: {repeat}")

            result = {
                "requested_model": model,
                "system_prompt": SYSTEM_PROMPT,
                "prompt": PROMPT,
                "temperature": temperature,
                "repeat": repeat,
                "max_output_tokens": 512,
            }

            start = perf_counter()

            try:
                response = client.responses.create(
                    model=model,
                    instructions=SYSTEM_PROMPT,
                    input=PROMPT,
                    temperature=temperature,
                    max_output_tokens=512,
                )

                result.update({
                    "elapsed_seconds": round(perf_counter() - start, 3),
                    "response_model": response.model,
                    "status": response.status,
                    "answer": response.output_text,
                    "usage": (
                        response.usage.model_dump()
                        if response.usage else None
                    ),
                    "incomplete_details": (
                        response.incomplete_details.model_dump()
                        if response.incomplete_details else None
                    ),
                })

                print(result["answer"])
                print(f"время: {result['elapsed_seconds']} с")
                print(f"статус: {result['status']}")

            except OpenAIError as error:
                result.update({
                    "elapsed_seconds": round(perf_counter() - start, 3),
                    "status": "error",
                    "error": str(error),
                })
                print("Ошибка API:", error)

            filename = f"temp_{temperature}_repeat_{repeat}.json"
            (output_dir / filename).write_text(
                json.dumps(result, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    print("\nэксперимент завершен. результаты сохранены.")


if __name__ == "__main__":
    main()