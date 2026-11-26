from dataclasses import dataclass
from pathlib import Path

from docx import Document
from docx.table import Table


@dataclass
class ParsedDocument:
    source: Path
    blocks: list[str]


def _table_rows(table: Table) -> list[str]:
    rows = []
    for row in table.rows:
        cells = []
        for cell in row.cells:
            text = cell.text.strip()
            if text and (not cells or cells[-1] != text):
                cells.append(text)
        if cells:
            rows.append(" | ".join(cells))
    return rows


def parse_docx(path: Path) -> ParsedDocument:
    blocks = []
    for item in Document(str(path)).iter_inner_content():
        if isinstance(item, Table):
            rows = _table_rows(item)
            if rows:
                blocks.append("\n".join(rows))
        else:
            text = item.text.strip()
            if text:
                blocks.append(text)
    return ParsedDocument(source=path, blocks=blocks)


def load_documents(folder: Path) -> list[ParsedDocument]:
    return [parse_docx(path) for path in sorted(folder.glob("*.docx")) if not path.name.startswith("~$")]
