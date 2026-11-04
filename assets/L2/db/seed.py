from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Enclosure
from db.session import Base, SessionLocal, engine

# Для своего варианта замените состав справочника.
SEED = (
    ("ENC-01", "Кролики", "кролик"),
    ("ENC-02", "Черепахи", "черепаха"),
    ("ENC-03", "Попугаи", "волнистый попугай"),
    ("ENC-04", "Морские свинки", "морская свинка"),
    ("ENC-05", "Аквариум", "гуппи"),
    ("ENC-06", "Ахатины", "ахатина"),
)


def seed_enclosures(db: Session) -> None:
    existing = set(db.scalars(select(Enclosure.code)))
    for code, name, species in SEED:
        if code not in existing:
            db.add(Enclosure(code=code, name=name, species=species))
    db.commit()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_enclosures(db)
