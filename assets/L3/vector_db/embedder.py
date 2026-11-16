import sys
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from vector_db.chunker import TEMP_DIR, TOKENIZER_NAME, Chunk, build_temp_chunks

ROOT = Path(__file__).resolve().parent.parent
QDRANT_DIR = ROOT / "qdrant"
COLLECTION = "docs"

_model = None


def load_chunks(temp_dir: Path = TEMP_DIR) -> list[Chunk]:
    paths = sorted(temp_dir.glob("*.txt"), key=_chunk_sort_key)
    if not paths:
        paths = build_temp_chunks(temp_dir=temp_dir)
    chunks: list[Chunk] = []
    for path in paths:
        stem, number = path.stem.rsplit("_", 1)
        chunks.append(
            Chunk(
                source=Path(f"{stem}.docx"),
                number=int(number),
                text=path.read_text(encoding="utf-8"),
            )
        )
    return chunks


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    vectors = _get_model().encode(
        texts,
        batch_size=4,
        normalize_embeddings=True,
        show_progress_bar=False,
        convert_to_numpy=True,
    )
    return [vector.tolist() for vector in vectors]


def fill_database(temp_dir: Path = TEMP_DIR) -> int:
    chunks = load_chunks(temp_dir)
    if not chunks:
        return 0

    vectors = embed_texts([chunk.text for chunk in chunks])
    client = QdrantClient(path=str(QDRANT_DIR))
    try:
        if client.collection_exists(COLLECTION):
            client.delete_collection(COLLECTION)
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=len(vectors[0]), distance=Distance.COSINE),
        )
        client.upsert(
            collection_name=COLLECTION,
            points=[
                PointStruct(
                    id=index,
                    vector=vector,
                    payload={
                        "source": chunk.source.name,
                        "chunk": chunk.number,
                        "text": chunk.text,
                    },
                )
                for index, (chunk, vector) in enumerate(zip(chunks, vectors), start=1)
            ],
        )
    finally:
        client.close()
    return len(chunks)


def search(query: str, limit: int = 3) -> list[dict]:
    vector = embed_texts([query])[0]
    client = QdrantClient(path=str(QDRANT_DIR))
    try:
        found = client.query_points(
            collection_name=COLLECTION,
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


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(TOKENIZER_NAME)
    return _model


def warmup() -> None:
    _get_model()


def index_documents() -> int:
    build_temp_chunks()
    return fill_database()


def _chunk_sort_key(path: Path) -> tuple[str, int]:
    stem, number = path.stem.rsplit("_", 1)
    return stem, int(number)


if __name__ == "__main__":
    count = index_documents()
    print(f"{count} points -> {COLLECTION}")
