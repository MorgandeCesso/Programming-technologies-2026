from dataclasses import dataclass
from functools import lru_cache

from transformers import AutoTokenizer

from app.logic.documents import ParsedDocument


TOKENIZER_NAME = "BAAI/bge-m3"
CHUNK_SIZE = 600
CHUNK_OVERLAP = 60


@dataclass(frozen=True)
class Chunk:
    source: str
    number: int
    text: str
    token_count: int


@lru_cache(maxsize=1)
def get_tokenizer():
    return AutoTokenizer.from_pretrained(
        TOKENIZER_NAME,
        use_fast=True,
    )


def make_chunks(
    document: ParsedDocument,
    size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[Chunk]:
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError("нужно: size > 0 и 0 <= overlap < size")

    if not document.text.strip():
        return []

    tokenizer = get_tokenizer()
    encoded = tokenizer(
        document.text,
        add_special_tokens=False,
        return_offsets_mapping=True,
        truncation=False,
    )
    offsets = encoded["offset_mapping"]

    chunks = []
    start = 0
    step = size - overlap

    while start < len(offsets):
        end = min(start + size, len(offsets))

        # позиции токенов используем для вырезания исходного текста
        char_start = offsets[start][0]
        char_end = offsets[end - 1][1]
        text = document.text[char_start:char_end]

        if text.strip():
            chunks.append(
                Chunk(
                    source=document.source,
                    number=len(chunks) + 1,
                    text=text,
                    token_count=end - start,
                )
            )

        if end == len(offsets):
            break

        start += step

    return chunks