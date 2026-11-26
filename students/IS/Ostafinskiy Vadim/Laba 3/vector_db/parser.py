from dataclasses import dataclass
from pathlib import Path
from docx import Document
from docx.document import Document as DocumentObject
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

@dataclass(frozen=True)
class Block:
    kind: str
    text: str

@dataclass(frozen=True)
class ParsedDocument:
    source: Path
    blocks: list[Block]

def parse_docx(path: str | Path) -> ParsedDocument:
    source = Path(path)
    document = Document(source)
    blocks = [_to_block(item) for item in _iter_blocks(document)]

    return ParsedDocument(
        source=source,
        blocks=[block for block in blocks if block is not None],
    )

def _iter_blocks(document: DocumentObject):
    for child in document.element.body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, document)
        elif child.tag == qn("w:tbl"):
            yield Table(child, document)

def _to_block(item: Paragraph | Table) -> Block | None:
    if isinstance(item, Paragraph):
        text = " ".join(item.text.split())
        if not text:
            return None
        return Block(kind=_paragraph_kind(item), text=text)

    text = _table_text(item)
    if not text:
        return None
    return Block(kind="table", text=text)

def _paragraph_kind(paragraph: Paragraph) -> str:
    style_id = paragraph.style.style_id if paragraph.style is not None else ""

    if style_id == "Title":
        return "title"
    if style_id == "Caption":
        return "caption"
    if style_id.startswith("Heading"):
        return "heading"

    return "paragraph"

def _table_text(table: Table) -> str:
    lines: list[str] = []

    for row in table.rows:
        cells = [" ".join(cell.text.split()) for cell in row.cells]
        if any(cells):
            lines.append(" | ".join(cells))

    return "\n".join(lines)
