import json

from app.clients.embeddings import embed_texts
from app.config import TEMP_DIR
from app.db.vector_store import replace_index


def main():
    manifest = TEMP_DIR / "chunks.json"

    if not manifest.exists():
        raise ValueError("сначала запусти scripts.prepare_documents")

    chunks = json.loads(manifest.read_text(encoding="utf-8"))
    if not chunks:
        raise ValueError("список чанков пуст")

    print("прочитано чанков:", len(chunks))
    print("получаем эмбеддинги...")

    vectors = embed_texts([chunk["text"] for chunk in chunks])
    print("размерность:", len(vectors[0]))

    count = replace_index(chunks, vectors)
    print("сохранено точек в Qdrant:", count)


if __name__ == "__main__":
    main()