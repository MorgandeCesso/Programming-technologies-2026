import sys, time, json
from lab1 import client, SYSTEM, PROMPTS 


def ask(model, prompt, temperature=0.7):
    t0 = time.perf_counter()
    r = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=4000,
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
    for name in ("bug", "json"):
        print("запрос:", name)
        results[name] = ask(model, PROMPTS[name])
        print("  finish_reason:", results[name]["finish_reason"],
              "| токенов:", results[name]["tokens"],
              "| время:", results[name]["time_s"], "с")
    with open(f"rerun_{model}.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("Готово")
