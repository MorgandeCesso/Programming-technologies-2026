import json
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from openai import APIConnectionError, APITimeoutError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Suggestion


test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

Base.metadata.create_all(bind=test_engine)
TestSession = sessionmaker(bind=test_engine)


def override_get_db():
    with TestSession() as db:
        yield db


def count_records():
    with TestSession() as db:
        return db.query(Suggestion).count()


def model_response(content):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                finish_reason="stop",
                message=SimpleNamespace(content=content),
            )
        ]
    )


def check_error(response, expected_status, expected_code):
    assert response.status_code == expected_status, response.text

    body = response.json()

    assert set(body) == {"error"}, body
    assert set(body["error"]) == {"code", "message"}, body
    assert body["error"]["code"] == expected_code, body
    assert isinstance(body["error"]["message"], str), body
    assert body["error"]["message"].strip(), body


def main():
    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db

    valid_data = {
        "category": "practice",
        "summary": "предложение добавить задания",
        "course_code": None,
        "topic": None,
        "requested_change": "добавить задания",
        "details": None,
    }

    try:
        with TestClient(app) as client:
            with patch(
                "app.llm.client.chat.completions.create"
            ) as model_mock:

                for field in valid_data:
                    incomplete_data = valid_data.copy()
                    del incomplete_data[field]

                    model_mock.return_value = model_response(
                        json.dumps(incomplete_data)
                    )

                    before = count_records()

                    response = client.post(
                        "/suggestions",
                        json={"message": "добавить задания"},
                    )

                    check_error(
                        response,
                        502,
                        "invalid_model_response",
                    )

                    assert count_records() == before
                    print(f"пропущен ключ {field}: 502, не сохранено")

                invalid_responses = {
                    "невалидный JSON": "это не JSON",
                    "лишнее поле": json.dumps(
                        {**valid_data, "extra": "лишнее"}
                    ),
                    "пустой summary": json.dumps(
                        {**valid_data, "summary": "   "}
                    ),
                    "список вместо строки": json.dumps(
                        {**valid_data, "topic": ["SQL"]}
                    ),
                    "неизвестная категория": json.dumps(
                        {**valid_data, "category": "unknown"}
                    ),
                }

                for name, content in invalid_responses.items():
                    model_mock.return_value = model_response(content)
                    before = count_records()

                    response = client.post(
                        "/suggestions",
                        json={"message": "добавить задания"},
                    )

                    check_error(
                        response,
                        502,
                        "invalid_model_response",
                    )

                    assert count_records() == before
                    print(f"{name}: 502, не сохранено")

                invalid_requests = [
                    {},
                    {"message": 123},
                    {"message": ""},
                    {"message": "   "},
                ]

                for payload in invalid_requests:
                    model_mock.reset_mock()
                    before = count_records()

                    response = client.post(
                        "/suggestions",
                        json=payload,
                    )

                    check_error(response, 422, "validation_error")
                    model_mock.assert_not_called()
                    assert count_records() == before

                print("неверные сообщения: 422, модель не вызвана")

                for error, status, code in [
                    (
                        APIConnectionError(request=None),
                        503,
                        "model_unavailable",
                    ),
                    (
                        APITimeoutError(request=None),
                        504,
                        "model_timeout",
                    ),
                ]:
                    model_mock.side_effect = error
                    before = count_records()

                    response = client.post(
                        "/suggestions",
                        json={"message": "добавить задания"},
                    )

                    check_error(response, status, code)
                    assert count_records() == before
                    print(f"ошибка модели: {status}, не сохранено")

                model_mock.side_effect = None
                model_mock.reset_mock()

                response = client.get("/suggestions/999999")
                check_error(response, 404, "not_found")
                model_mock.assert_not_called()

                print("отсутствующая запись: 404")

                model_mock.return_value = model_response(
                    json.dumps(valid_data)
                )

                response = client.post(
                    "/suggestions",
                    json={"message": "добавить задания"},
                )

                assert response.status_code == 201, response.text
                assert count_records() == 1
                assert response.json()["match_status"] == "not_provided"

                print("полный ответ с null: 201, сохранено")

        print("\nвсе проверки пройдены")

    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)
        test_engine.dispose()


if __name__ == "__main__":
    main()