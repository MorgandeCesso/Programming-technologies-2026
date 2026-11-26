from app.llm import extract_suggestion


message = (
    "мне нравится курс CS-204 по базам данных, "
    "но хотелось бы добавить больше практических заданий "
    "по SQL. Сейчас практики недостаточно."
)

try:
    result = extract_suggestion(message)

    print("результат извлечения:")
    print(result.model_dump_json(indent=4))

except Exception as error:
    print("тип ошибки:", type(error).__name__)
    print("описание:", error)
    print("дополнительная информация:", getattr(error, "body", None))