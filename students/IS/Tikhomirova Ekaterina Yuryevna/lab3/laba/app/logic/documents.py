from dataclasses import dataclass
from pathlib import Path

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph


@dataclass(frozen=True)
class ParsedDocument:
    source: str
    text: str


def read_document(path: Path) -> ParsedDocument:
    document = Document(path)
    blocks = []

    # сохраняем порядок абзацев и таблиц
    for item in document.iter_inner_content():
        if isinstance(item, Paragraph):
            text = item.text.strip()
            if text:
                blocks.append(text)

        elif isinstance(item, Table):
            rows = []

            for row in item.rows:
                values = [
                    cell.text.strip().replace("\n", " ")
                    for cell in row.cells
                ]

                if any(values):
                    rows.append(" | ".join(values))

            if rows:
                blocks.append("\n".join(rows))

    return ParsedDocument(
        source=path.name,
        text="\n\n".join(blocks),
    )