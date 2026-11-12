"""Настройки приложения. Всё берётся из переменных окружения или файла .env."""
import os

from dotenv import load_dotenv

load_dotenv()

# Подключение к локальной модели (LM Studio, OpenAI-совместимый API)
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://127.0.0.1:7000/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen3.5-4b")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "180"))          # секунды ожидания ответа
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4000"))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))

# База данных: PostgreSQL в Docker
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://lab2:lab2@127.0.0.1:5432/registrations"
)
