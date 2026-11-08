from unittest.mock import patch

from fastapi.testclient import TestClient
from openai import APITimeoutError

from app.main import app


client = TestClient(app)


with patch(
    "app.main.extract_suggestion",
    side_effect=APITimeoutError(request=None)
):
    response = client.post(
        "/suggestions",
        json={
            "message": "хотелось бы добавить больше практических заданий по Python"
        }
    )

print("статус:", response.status_code)
print("ответ:", response.json())
