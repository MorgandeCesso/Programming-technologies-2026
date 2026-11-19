from sqlalchemy import select
from sqlalchemy.orm import Session
from db.models import Service
from db.session import Base, SessionLocal, engine

SEED = (
    ("SV-001", "Изготовление изделий на заказ"),
    ("SV-002", "Ремонт одежды"),
    ("SV-003", "Ремонт мебели"),
    ("SV-004", "Ремонт бытовой техники"),
    ("SV-012", "Гравировка"),
    ("SV-015", "Персонализация изделий"),
)

def seed_services(db: Session) -> None:
    existing = set(db.scalars(select(Service.code)))

    for code, name in SEED:
        if code not in existing:
            db.add(Service(code=code, name=name))

    db.commit()

def init_db() -> None:
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        seed_services(db)
