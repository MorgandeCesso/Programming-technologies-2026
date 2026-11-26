from dataclasses import dataclass
from pathlib import Path

from app import config
from app.logic.documents import ParsedDocument


@dataclass
class Chunk:
    source: str
    number: int
    text: str


_tokenizer = None


def get_tokenizer():
    global _tokenizer
    if _tokenizer is None:
        from transformers import AutoTokenizer

        _tokenizer = AutoTokenizer.from_pretrained(config.TOKENIZER_NAME)
    return _tokenizer


def split_text(text: str, size: int, overlap: int, tokenizer=None) -> list[str]:
    if overlap >= size:
        raise ValueError("overlap должен быть меньше size")
    tokenizer = tokenizer or get_tokenizer()
    encoded = tokenizer(
        text,
        add_special_tokens=False,
        return_offsets_mapping=True,
        truncation=False,
    )
    offsets = encoded["offset_mapping"]

    pieces = []
    step = size - overlap
    start = 0
    total = len(offsets)
    while start < total:
        end = min(start + size, total)
        char_start = offsets[start][0]
        char_end = offsets[end - 1][1]
        pieces.append(text[char_start:char_end])
        if end == total:
            break
        start += step
    return pieces


def make_chunks(
    document: ParsedDocument,
    size: int = config.CHUNK_SIZE,
    overlap: int = config.CHUNK_OVERLAP,
    tokenizer=None,
) -> list[Chunk]:
    text = "\n\n".join(document.blocks)
    return [
        Chunk(source=document.source.stem, number=number, text=piece)
        for number, piece in enumerate(split_text(text, size, overlap, tokenizer), start=1)
    ]


def save_chunks(chunks: list[Chunk], folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("*.txt"):
        old.unlink()
    for chunk in chunks:
        (folder / f"{chunk.source}_{chunk.number}.txt").write_text(chunk.text, encoding="utf-8")


def load_chunks(folder: Path) -> list[Chunk]:
    chunks = []
    for path in folder.glob("*.txt"):
        source, number = path.stem.rsplit("_", 1)
        chunks.append(Chunk(source=source, number=int(number), text=path.read_text(encoding="utf-8")))
    return sorted(chunks, key=lambda chunk: (chunk.source, chunk.number))
