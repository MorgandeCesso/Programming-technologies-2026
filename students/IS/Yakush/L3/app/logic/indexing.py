from pathlib import Path

from app import config
from app.db import vector_store
from app.errors import IndexEmpty
from app.logic import chunking, embeddings
from app.logic.documents import load_documents


def fill_database(folder: Path | None = None) -> int:
    chunks = chunking.load_chunks(folder or config.TEMP_DIR)
    if not chunks:
        raise IndexEmpty("В docs/temp нет фрагментов для записи")
    vectors = embeddings.embed_texts([chunk.text for chunk in chunks])
    payloads = [{"source": chunk.source, "chunk": chunk.number, "text": chunk.text} for chunk in chunks]
    return vector_store.get_store().recreate(vectors, payloads)


def index_documents(source: Path | None = None, temp: Path | None = None) -> dict:
    temp = temp or config.TEMP_DIR
    documents = load_documents(source or config.SOURCE_DIR)
    chunks = [chunk for document in documents for chunk in chunking.make_chunks(document)]
    chunking.save_chunks(chunks, temp)
    stored = fill_database(temp)
    return {"documents": len(documents), "chunks": stored}


def search(query: str, limit: int | None = None) -> list[dict]:
    vector = embeddings.embed_texts([query])[0]
    return vector_store.get_store().search(vector, limit or config.SEARCH_LIMIT)
