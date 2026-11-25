from dataclasses import dataclass
from pathlib import Path
from transformers import AutoTokenizer
from vector_db.parser import ParsedDocument, parse_docx

ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "docs"
TEMP_DIR = DOCS_DIR / "temp"
TOKENIZER_NAME = "BAAI/bge-m3"
CHUNK_SIZE = 200
CHUNK_OVERLAP = 20

_tokenizer = None

@dataclass(frozen=True)
class Chunk:
    source: Path
    number: int
    text: str

def make_chunks(
    document: ParsedDocument,
    size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[Chunk]:
    text = "\n\n".join(block.text for block in document.blocks)
    return [
        Chunk(source=document.source, number=number, text=piece)
        for number, piece in enumerate(
            _split_text(text, size, overlap), start=1
        )
    ]

def write_chunks(
    chunks: list[Chunk],
    temp_dir: Path = TEMP_DIR,
) -> list[Path]:
    temp_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for chunk in chunks:
        path = temp_dir / f"{chunk.source.stem}_{chunk.number}.txt"
        path.write_text(chunk.text, encoding="utf-8")
        written.append(path)
    return written

def build_temp_chunks(
    docs_dir: Path = DOCS_DIR,
    temp_dir: Path = TEMP_DIR,
) -> list[Path]:
    temp_dir.mkdir(parents=True, exist_ok=True)
    for old in temp_dir.glob("*.txt"):
        old.unlink()
    written: list[Path] = []
    for path in sorted(docs_dir.glob("*.docx")):
        document = parse_docx(path)
        chunks = make_chunks(document)
        written.extend(write_chunks(chunks, temp_dir))
    return written

def _split_text(text: str, size: int, overlap: int) -> list[str]:
    if size <= 0:
        raise ValueError("Размер чанка должен быть положительным")
    if overlap < 0 or overlap >= size:
        raise ValueError("Некорректный размер перекрытия")
    if not text:
        return []
    tokenizer = _get_tokenizer()
    encoded = tokenizer(
        text,
        add_special_tokens=False,
        return_offsets_mapping=True,
        truncation=False,
    )
    offsets = encoded["offset_mapping"]
    if not offsets:
        return []
    step = size - overlap
    pieces: list[str] = []
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

def _get_tokenizer():
    global _tokenizer
    if _tokenizer is None:
        _tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_NAME)
    return _tokenizer

if __name__ == "__main__":
    for path in build_temp_chunks():
        print(path.relative_to(ROOT))
