from app.logic.crag import ask_crag
from app.logic.rag import ask_rag


def ask(
    message: str,
    mode: str = "rag",
    limit: int = 3,
) -> dict:
    if mode == "rag":
        return ask_rag(message, limit=limit)

    if mode == "crag":
        return ask_crag(message, limit=limit)

    raise ValueError("неизвестный режим обработки")