import json
from dataclasses import asdict
from pathlib import Path

from app.logic.chunking import make_chunks
from app.logic.documents import read_document


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "docs" / "source"
TEMP_DIR = ROOT / "docs" / "temp"


def main():
    paths = sorted(
        path
        for path in SOURCE_DIR.glob("*.docx")
        if not path.name.startswith("~$")
    )

    if not paths:
        raise ValueError("в docs/source нет документов .docx")

    # сначала обрабатываем все документы, затем сохраняем результат
    all_chunks = []

    for path in paths:
        document = read_document(path)
        chunks = make_chunks(document)

        print(f"{path.name}: фрагментов — {len(chunks)}")
        all_chunks.extend(chunks)

    if not all_chunks:
        raise ValueError("документы не содержат текста")

    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    for chunk in all_chunks:
        filename = (
            f"{Path(chunk.source).stem}_chunk_{chunk.number}.txt"
        )
        (TEMP_DIR / filename).write_text(
            chunk.text,
            encoding="utf-8",
        )

        print(
            f"  {filename}: "
            f"{chunk.token_count} токенов"
        )

    # этот файл будет использоваться при заполнении базы
    manifest = [asdict(chunk) for chunk in all_chunks]
    (TEMP_DIR / "chunks.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\nвсего фрагментов:", len(all_chunks))
    print("сохранено в:", TEMP_DIR)


if __name__ == "__main__":
    main()