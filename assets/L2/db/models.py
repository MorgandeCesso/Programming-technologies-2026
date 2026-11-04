from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from db.session import Base


class Enclosure(Base):
    """Справочник вольеров. Код не подменяет внутренний id."""

    __tablename__ = "enclosures"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    species: Mapped[str] = mapped_column(String(200), nullable=False)


class Note(Base):
    """Обработанное сообщение"""

    __tablename__ = "enclosure_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    enclosure_code: Mapped[str | None] = mapped_column(String(32))
    animal_text: Mapped[str | None] = mapped_column(Text)
    observation_text: Mapped[str | None] = mapped_column(Text)
    details: Mapped[str | None] = mapped_column(Text)
    enclosure_id: Mapped[int | None] = mapped_column(ForeignKey("enclosures.id"))
    match_status: Mapped[str] = mapped_column(String(32), nullable=False)
