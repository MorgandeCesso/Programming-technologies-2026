"""Подключение к базе данных и таблицы (SQLAlchemy ORM)."""
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from app.config import DATABASE_URL



connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


def normalize_code(code: str) -> str:
    """Одинаковое правило для кода из справочника и кода из сообщения:
    убираем внешние пробелы и приводим к верхнему регистру."""
    return code.strip().upper()


class Event(Base):
    """Справочник: мероприятия."""
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)            # внутренний ID
    code: Mapped[str] = mapped_column(String(50), unique=True)    # уникальный код 
    title: Mapped[str] = mapped_column(String(200))               # наименование
    event_date: Mapped[str | None] = mapped_column(String(50))    # доп. характеристики
    location: Mapped[str | None] = mapped_column(String(200))


class Registration(Base):
    """Обработанные сообщения: намерения участия."""
    __tablename__ = "registrations"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    message: Mapped[str] = mapped_column(Text)                    # исходный текст

    # шесть полей, извлечённых моделью
    category: Mapped[str] = mapped_column(String(20))
    summary: Mapped[str] = mapped_column(Text)
    event_code: Mapped[str | None] = mapped_column(String(50))    # как извлекла модель
    participant_name: Mapped[str | None] = mapped_column(String(200))
    participation_format: Mapped[str | None] = mapped_column(String(100))
    details: Mapped[str | None] = mapped_column(Text)

    # результат сопоставления со справочником
    event_id: Mapped[int | None] = mapped_column(ForeignKey("events.id"))
    match_status: Mapped[str] = mapped_column(String(20))         # matched / not_found / not_provided


def init_db() -> None:
    Base.metadata.create_all(engine)


def get_db():
    """Зависимость FastAPI: открывает сессию на время запроса и закрывает после."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
