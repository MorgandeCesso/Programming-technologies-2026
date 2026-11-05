import os, sys, time, json
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:7000/v1",
    api_key=os.environ["LMSTUDIO_API_KEY"],
)

SYSTEM = "Отвечай по-русски. Если информации недостаточно, сообщи об этом."

PROMPTS = {
    "concept": "Объясни, что такое рекурсия в программировании, коротко и с примером.",
    "function": "Напиши на Python функцию, которая проверяет, является ли строка палиндромом (без учёта регистра и пробелов).",
    "bug": "Найди ошибку в коде и исправь:\n\ndef avg(nums):\n    total = 0\n    for n in nums:\n        total += n\n    return total / len(nums) + 1\n\nprint(avg([]))",
    "json": "Из текста извлеки данные и верни ТОЛЬКО JSON с полями name, city, age:\n'Иван Петров, 34 года, живёт в Томске и работает инженером.'",
    "no_answer": "Текст: 'Кошка спит на подоконнике.' Вопрос: какого цвета у кошки глаза?",
}

def ask(model, prompt, temperature=0.7):
    t0 = time.perf_counter()
    r = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=1500,
    )
    dt = time.perf_counter() - t0
    msg = r.choices[0].message
    return {
        "temperature": temperature,
        "time_s": round(dt, 2),
        "tokens": r.usage.completion_tokens,
        "finish_reason": r.choices[0].finish_reason,
        "answer": msg.content,
        "reasoning": getattr(msg, "reasoning_content", None),
    }

if __name__ == "__main__":
    model = sys.argv[1]
    results = {}

    # Эксперимент 1: 5 запросов, одинаковые настройки (temperature=0.7)
    for name, p in PROMPTS.items():
        print("запрос:", name)
        results[name] = ask(model, p)

    # Эксперимент 2: влияние температуры (один запрос по 3 раза)
    for temp in (0.2, 1.0):
        results[f"temp_{temp}"] = []
        for i in range(3):
            print(f"температура {temp}, прогон {i + 1}")
            results[f"temp_{temp}"].append(ask(model, PROMPTS["concept"], temp))

    with open(f"results_{model}.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("Готово")