
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey
)

from app.database import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)


class Suggestion(Base):
    __tablename__ = "suggestions"

    id = Column(Integer, primary_key=True, index=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    original_message = Column(Text, nullable=False)

    category = Column(String(50), nullable=False)
    summary = Column(Text, nullable=False)
    course_code = Column(String(50), nullable=True)
    topic = Column(Text, nullable=True)
    requested_change = Column(Text, nullable=True)
    details = Column(Text, nullable=True)

    course_id = Column(
        Integer,
        ForeignKey("courses.id"),
        nullable=True
    )

    match_status = Column(String(20), nullable=False)
