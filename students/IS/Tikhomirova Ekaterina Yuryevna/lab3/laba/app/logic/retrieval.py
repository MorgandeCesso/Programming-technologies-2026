from app.clients.embeddings import embed_texts
from app.db.vector_store import search_vectors


def search(query: str, limit: int = 3) -> list[dict]:
    query = query.strip()

    if not query:
        raise ValueError("поисковый запрос не должен быть пустым")

    vector = embed_texts([query])[0]
    return search_vectors(vector, limit=limit)