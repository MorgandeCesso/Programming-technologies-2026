import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from time import perf_counter

from dotenv import load_dotenv
from openai import APIConnectionError, APIStatusError, DefaultHttpxClient, OpenAI


PROJECT_DIR = Path(__file__).resolve().parent
MAX_OUTPUT_TOKENS = 256
BASE_TEMPERATURE = 0.2

NOTICE = (
    "В субботу клуб «Маяк» проводит мастер-класс «Основы Python» в кабинете 204. "
    "Начало в 14:30. Записалось 12 участников."
)

PROMPTS = {
    "concept": (
        "Объясни начинающему программисту, что такое стек. "
        "Ответь ровно двумя предложениями по-русски. "
        "Укажи принцип LIFO и приведи один бытовой пример."
    ),
    "python": (
        "Напиши функцию sum_positive(numbers) на Python. На входе список целых чисел. "
        "Верни сумму элементов, строго больших нуля. Для пустого списка верни 0. "
        "Ответь только кодом Python, без Markdown, объяснений и примеров вызова."
    ),
    "debug": (
        "Объясни, почему этот код вызывает IndexError, и предложи исправленную строку цикла. "
        "Ответь двумя строками: причина и исправленная строка.\n"
        "numbers = [10, 20, 30]\n"
        "for i in range(len(numbers) + 1):\n"
        "    print(numbers[i])"
    ),
    "json": (
        f"Текст: {NOTICE}\n"
        'Извлеки данные в объект JSON с ключами "event", "room", "start", "participants". '
        "event — название мероприятия, room — номер кабинета целым числом, "
        "start — время строкой в формате ЧЧ:ММ, participants — число участников целым числом. "
        "Верни только объект JSON без Markdown."
    ),
    "missing": (
        f"Текст: {NOTICE}\n"
        "Как зовут преподавателя мастер-класса? Отвечай только по этому тексту, одним предложением. "
        "Если информации недостаточно, сообщи об этом."
    ),
}


def ask(client, model, prompt, temperature):
    start = perf_counter()
    response = client.responses.create(
        model=model,
        input=prompt,
        temperature=temperature,
        top_p=1.0,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        store=False,
    )
    return {
        "seconds": round(perf_counter() - start, 3),
        "status": response.status,
        "answer": response.output_text,
        "output_tokens": response.usage.output_tokens if response.usage else None,
    }


def main():
    parser = argparse.ArgumentParser(description="Замеры локальных моделей в LM Studio.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--list", action="store_true", help="Вывести идентификаторы моделей.")
    mode.add_argument("--model", help="Идентификатор загруженной модели из LM Studio.")
    parser.add_argument("--temperature-test", action="store_true", help="По три прогона при 0.2 и 1.0.")
    parser.add_argument("--output", type=Path, help="Путь к JSON с результатами.")
    args = parser.parse_args()
    if args.model and args.output is None:
        parser.error("Укажите --output для сохранения замеров.")
    if args.list and (args.temperature_test or args.output):
        parser.error("Опции --temperature-test и --output используются с --model.")

    load_dotenv(PROJECT_DIR / ".env", encoding="utf-8-sig")
    token = os.getenv("LM_STUDIO_API_TOKEN", "").strip()
    if not token:
        parser.error("Заполните LM_STUDIO_API_TOKEN в .env.")
    try:
        port = int(os.getenv("LM_STUDIO_PORT", "1234"))
        if not 1 <= port <= 65535:
            raise ValueError
    except ValueError:
        parser.error("LM_STUDIO_PORT должен быть целым числом от 1 до 65535.")

    with OpenAI(
        base_url=f"http://127.0.0.1:{port}/v1",
        api_key=token,
        timeout=180,
        max_retries=0,
        http_client=DefaultHttpxClient(trust_env=False, follow_redirects=False),
    ) as client:
        try:
            model_ids = [model.id for model in client.models.list().data]
            if args.list:
                print("Модели, доступные через API")
                for model_id in model_ids:
                    print(f"  {model_id}")
                return 0
            if args.model not in model_ids:
                parser.error("Модель отсутствует в списке API. Проверьте идентификатор через --list.")

            print(f"Прогрев модели {args.model}…", flush=True)
            warmup = ask(client, args.model, "Ответь одним словом: готово.", BASE_TEMPERATURE)
            if warmup["status"] != "completed" or not warmup["answer"].strip():
                raise SystemExit("Модель не завершила пробный запрос. Проверьте логи в LM Studio.")
            if args.temperature_test:
                trials = [
                    ("concept", temperature, repeat)
                    for repeat in range(1, 4)
                    for temperature in (0.2, 1.0)
                ]
            else:
                trials = [(name, BASE_TEMPERATURE, 1) for name in PROMPTS]

            results = {
                "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
                "model": args.model,
                "endpoint": "/v1/responses",
                "max_output_tokens": MAX_OUTPUT_TOKENS,
                "top_p": 1.0,
                "expected_trials": len(trials),
                "trials": [],
            }
            args.output.parent.mkdir(parents=True, exist_ok=True)
            for name, temperature, repeat in trials:
                print(f"{name} | temperature={temperature} | попытка {repeat}", flush=True)
                prompt = PROMPTS[name]
                result = ask(client, args.model, prompt, temperature)
                results["trials"].append({
                    "task": name,
                    "temperature": temperature,
                    "repeat": repeat,
                    "prompt": prompt,
                    **result,
                })
                args.output.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                print(f'{result["seconds"]:.3f} с | {result["status"]}\n{result["answer"]}\n', flush=True)
        except APIConnectionError:
            raise SystemExit(f"Нет ответа от LM Studio. Проверьте сервер и порт {port}.") from None
        except APIStatusError as error:
            raise SystemExit(f"LM Studio вернула HTTP {error.status_code}. Проверьте токен и логи сервера.") from None

    print(f"Замеры сохранены в {args.output.resolve()}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
