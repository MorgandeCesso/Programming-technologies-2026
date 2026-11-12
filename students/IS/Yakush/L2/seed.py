"""Заполнение справочника мероприятий учебными записями.

Запуск: python seed.py
Повторный запуск ничего не дублирует: запись добавляется, только если такого кода ещё нет.
"""
from sqlalchemy import select

from app.db import Event, SessionLocal, init_db, normalize_code

EVENTS = [
    {"code": "EVT-026", "title": "Конференция «LLM в образовании»", "event_date": "2026-11-20", "location": "главный корпус, ауд. 301"},
    {"code": "EVT-101", "title": "Хакатон по анализу данных", "event_date": "2026-11-28", "location": "коворкинг, 2 этаж"},
    {"code": "EVT-115", "title": "Митап Python-разработчиков", "event_date": "2026-12-03", "location": "онлайн"},
    {"code": "EVT-204", "title": "Лекция «Введение в Docker»", "event_date": "2026-12-10", "location": "главный корпус, ауд. 210"},
    {"code": "EVT-310", "title": "Ярмарка вакансий IT-компаний", "event_date": "2026-12-17", "location": "актовый зал"},
]


def seed() -> None:
    init_db()
    with SessionLocal() as db:
        added = 0
        for item in EVENTS:
            code = normalize_code(item["code"])
            if db.scalar(select(Event).where(Event.code == code)) is None:
                db.add(Event(**{**item, "code": code}))
                added += 1
        db.commit()
        total = len(db.scalars(select(Event)).all())
    print(f"Добавлено мероприятий: {added}, всего в справочнике: {total}")


if __name__ == "__main__":
    seed()
