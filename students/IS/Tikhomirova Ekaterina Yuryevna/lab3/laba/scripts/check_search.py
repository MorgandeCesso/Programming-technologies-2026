import sys

from app.logic.retrieval import search


def main():
    question = " ".join(sys.argv[1:]).strip()

    if not question:
        question = "когда измерение считается устаревшим?"

    print("вопрос:", question)

    results = search(question)

    for number, item in enumerate(results, start=1):
        print(f"\nрезультат {number}")
        print("источник:", item["source"])
        print("номер чанка:", item["chunk"])
        print("сходство:", round(item["score"], 4))
        print("текст:")
        print(item["text"])


if __name__ == "__main__":
    main()