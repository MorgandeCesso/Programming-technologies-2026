from threading import RLock

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.config import COLLECTION, EMBEDDING_MODEL, QDRANT_DIR


DB_LOCK = RLock()


def replace_index(
    chunks: list[dict],
    vectors: list[list[float]],
) -> int:
    if not chunks or len(chunks) != len(vectors):
        raise ValueError("число чанков не совпадает с числом векторов")

    dimension = len(vectors[0])
    if dimension == 0 or any(len(v) != dimension for v in vectors):
        raise ValueError("некорректная размерность векторов")

    points = [
        PointStruct(
            id=index,
            vector=vector,
            payload={
                "source": chunk["source"],
                "chunk": chunk["number"],
                "text": chunk["text"],
                "embedding_model": EMBEDDING_MODEL,
            },
        )
        for index, (chunk, vector) in enumerate(
            zip(chunks, vectors), start=1
        )
    ]

    with DB_LOCK:
        client = QdrantClient(path=str(QDRANT_DIR))
        try:
            # при повторной индексации заменяем только нашу коллекцию
            if client.collection_exists(COLLECTION):
                client.delete_collection(COLLECTION)

            client.create_collection(
                collection_name=COLLECTION,
                vectors_config=VectorParams(
                    size=dimension,
                    distance=Distance.COSINE,
                ),
            )

            client.upsert(
                collection_name=COLLECTION,
                points=points,
                wait=True,
            )

            return client.count(
                collection_name=COLLECTION,
                exact=True,
            ).count
        finally:
            client.close()


def search_vectors(
    vector: list[float],
    limit: int = 3,
) -> list[dict]:
    if not 1 <= limit <= 20:
        raise ValueError("limit должен быть от 1 до 20")

    with DB_LOCK:
        client = QdrantClient(path=str(QDRANT_DIR))
        try:
            if not client.collection_exists(COLLECTION):
                raise ValueError("база не заполнена: выполни индексацию")

            collection = client.get_collection(COLLECTION)
            if collection.config.params.vectors.size != len(vector):
                raise ValueError(
                    "размерность изменилась: нужна повторная индексация"
                )

            result = client.query_points(
                collection_name=COLLECTION,
                query=vector,
                limit=limit,
                with_payload=True,
            )

            hits = []

            for point in result.points:
                payload = point.payload or {}

                if payload.get("embedding_model") != EMBEDDING_MODEL:
                    raise ValueError(
                        "модель эмбеддингов изменилась: "
                        "нужна повторная индексация"
                    )

                hits.append({
                    "score": float(point.score),
                    "source": payload["source"],
                    "chunk": payload["chunk"],
                    "text": payload["text"],
                })

            return hits
        finally:
            client.close()