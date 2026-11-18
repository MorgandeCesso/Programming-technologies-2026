
from sqlalchemy.orm import Session

from app.database import engine, Base, SessionLocal
from app.models import Course


# учебные курсы для справочника
COURSES = [
    {
        "code": "CS-101",
        "name": "основы программирования",
        "description": "изучение базовых конструкций программирования и алгоритмов."
    },
    {
        "code": "CS-204",
        "name": "базы данных",
        "description": "изучение реляционных баз данных и языка SQL."
    },
    {
        "code": "CS-305",
        "name": "разработка веб-приложений",
        "description": "разработка серверных и клиентских веб-приложений."
    },
    {
        "code": "CS-410",
        "name": "машинное обучение",
        "description": "изучение методов машинного обучения и нейронных сетей."
    },
    {
        "code": "CS-502",
        "name": "информационные системы",
        "description": "проектирование и разработка информационных систем."
    }
]


def seed_courses(db: Session):
    for course_data in COURSES:
        normalized_code = course_data["code"].strip().upper()

        existing_course = db.query(Course).filter(
            Course.code == normalized_code
        ).first()

        if existing_course is None:
            course = Course(
                code=normalized_code,
                name=course_data["name"],
                description=course_data["description"]
            )
            db.add(course)

    db.commit()


def main():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        seed_courses(db)
        print("справочник учебных курсов успешно заполнен!")

        courses = db.query(Course).order_by(Course.id).all()

        print("\nсписок курсов:")
        for course in courses:
            print(
                f"id: {course.id} | "
                f"код: {course.code} | "
                f"название: {course.name}"
            )

    finally:
        db.close()


if __name__ == "__main__":
    main()

