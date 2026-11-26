from app.database import SessionLocal
from app.models import Suggestion


db = SessionLocal()

try:
    suggestions = db.query(Suggestion).order_by(Suggestion.id).all()

    for item in suggestions:
        print(
            f"id: {item.id} | "
            f"код: {item.course_code} | "
            f"курс id: {item.course_id} | "
            f"статус: {item.match_status}"
        )
finally:
    db.close()
    