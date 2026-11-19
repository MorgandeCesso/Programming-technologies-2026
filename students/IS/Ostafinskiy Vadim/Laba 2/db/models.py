from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from db.session import Base

class Service(Base):
    __tablename__ = "services"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)


class WorkshopOrder(Base):
    __tablename__ = "workshop_orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)

    service_code: Mapped[str | None] = mapped_column(String(32))
    item_description: Mapped[str | None] = mapped_column(Text)
    deadline_text: Mapped[str | None] = mapped_column(Text)
    details: Mapped[str | None] = mapped_column(Text)

    service_id: Mapped[int | None] = mapped_column(
        ForeignKey("services.id")
    )
    
    match_status: Mapped[str] = mapped_column(String(32), nullable=False)
