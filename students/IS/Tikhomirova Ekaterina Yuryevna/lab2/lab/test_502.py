from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


with patch(
    "app.main.extract_suggestion",
    side_effect=ValueError("модель вернула некорректный JSON")
):
    response = client.post(
        "/suggestions",
        json={
            "message": "хотелось бы добавить больше практических заданий"
        }
    )

print("статус:", response.status_code)
print("ответ:", response.json())
