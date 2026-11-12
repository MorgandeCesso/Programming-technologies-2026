from pydantic import BaseModel

CATEGORIES = ("manufacture", "repair", "customization", "other")


def empty_to_none(value):
    if value is None:
        return None
    if not isinstance(value, str):
        return value
    value = value.strip()
    if value == "":
        return None
    return value


class OrderData(BaseModel):
    category: str
    summary: str
    service_code: str | None
    item_description: str | None
    deadline_text: str | None
    details: str | None


def check_order(data: dict):
    if set(data) != set(OrderData.model_fields):
        raise ValueError("В ответе должны быть ровно шесть полей")

    data = {
        "category": data["category"],
        "summary": data["summary"].strip() if isinstance(data["summary"], str) else data["summary"],
        "service_code": empty_to_none(data["service_code"]),
        "item_description": empty_to_none(data["item_description"]),
        "deadline_text": empty_to_none(data["deadline_text"]),
        "details": empty_to_none(data["details"]),
    }
    order = OrderData.model_validate(data)

    if order.category not in CATEGORIES:
        raise ValueError("Недопустимая категория")
    if order.summary == "":
        raise ValueError("Краткое содержание пустое")
    return order


if __name__ == "__main__":
    example = {
        "category": "customization",
        "summary": "Заказ гравировки на металлической фляге.",
        "service_code": "SV-012",
        "item_description": "Металлическая фляга",
        "deadline_text": "к 20 ноября",
        "details": "Текст гравировки: «За новые открытия!»",
    }

    print(check_order(example))

    bad = {
        "category": "price",
        "summary": "Хочу узнать цену",
        "service_code": "",
        "item_description": None,
        "deadline_text": None,
        "details": None,
    }

    try:
        check_order(bad)
    except ValueError as error:
        print("Плохой ответ отклонён:", error)