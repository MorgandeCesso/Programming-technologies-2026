from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).resolve().parent / ".env")

base_url = os.getenv("BASE_URL") or "https://openrouter.ai/api/v1"
system_prompt = os.getenv("SYSTEM_PROMPT") or ""

client = OpenAI(api_key=os.getenv("API_KEY"), base_url=base_url)

models = [
    {
        "name": "Nemotron",
        "slug": "nvidia/nemotron-3.5-super-vl:free",
        "temperature": 1.0,
        "reasoning": {"effort": "none"},
    },
    {
        "name": "Flint",
        "slug": "recursive/flint-v1.0:free",
    },
]


def get_response(text: str, model: dict, history: list) -> str:
    dialog = (history + [{"role": "user", "content": text}])[-6:]
    request = {
        "model": model["slug"],
        "input": dialog,
    }
    if "temperature" in model:
        request["temperature"] = model["temperature"]
    if "reasoning" in model:
        request["reasoning"] = model["reasoning"]
    if system_prompt:
        request["instructions"] = system_prompt

    response = client.responses.create(**request)
    answer = response.output_text or ""
    if not answer.strip(): 
        return ""

    history[:] = (dialog + [{"role": "assistant", "content": answer}])[-6:] # update history 
    return answer


if __name__ == "__main__":
    current = 0
    history = []
    print("Введите ваш вопрос (switch - другая модель, exit - выход):")
    print("Модель:", models[current]["name"])

    while True:
        question = input("Вы: ").strip()
        if not question:
            continue
        if question.lower() == "exit":
            print("Завершение программы")
            break
        if question.lower() == "switch":
            current = 1 - current
            history.clear()
            print("Модель:", models[current]["name"])
            continue

        try:
            answer = get_response(question, models[current], history)
        except Exception as exc:
            print("Ошибка запроса:", exc)
            continue

        if not answer:
            print("Модель вернула пустой ответ")
            continue
        print("Ответ:", answer)
