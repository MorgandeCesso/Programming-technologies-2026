import threading
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app import config
from app.errors import IndexEmpty


class VectorStore:
    def __init__(self, path: Path = config.QDRANT_DIR, collection: str = config.COLLECTION):
        self.path = path
        self.collection = collection
        self._lock = threading.Lock()

    def _client(self) -> QdrantClient:
        return QdrantClient(path=str(self.path))

    def recreate(self, vectors: list[list[float]], payloads: list[dict]) -> int:
        with self._lock:
            client = self._client()
            try:
                if client.collection_exists(self.collection):
                    client.delete_collection(self.collection)
                client.create_collection(
                    collection_name=self.collection,
                    vectors_config=VectorParams(size=len(vectors[0]), distance=Distance.COSINE),
                )
                client.upsert(
                    collection_name=self.collection,
                    points=[
                        PointStruct(id=index, vector=vector, payload=payload)
                        for index, (vector, payload) in enumerate(zip(vectors, payloads), start=1)
                    ],
                )
                return client.count(self.collection).count
            finally:
                client.close()

    def search(self, vector: list[float], limit: int) -> list[dict]:
        with self._lock:
            client = self._client()
            try:
                if not client.collection_exists(self.collection):
                    raise IndexEmpty("База знаний пуста, сначала вызовите /index")
                found = client.query_points(
                    collection_name=self.collection,
                    query=vector,
                    limit=limit,
                    with_payload=True,
                )
            finally:
                client.close()
        return [
            {
                "score": point.score,
                "source": point.payload.get("source"),
                "chunk": point.payload.get("chunk"),
                "text": point.payload.get("text", ""),
            }
            for point in found.points
        ]


_store: VectorStore | None = None


def get_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
