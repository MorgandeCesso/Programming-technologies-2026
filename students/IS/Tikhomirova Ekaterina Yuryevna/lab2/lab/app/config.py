import os
from dotenv import load_dotenv

load_dotenv()

LLM_BASE_URL = os.getenv(
    "LLM_BASE_URL",
    "http://127.0.0.1:1234/v1"
)

LLM_MODEL = os.getenv(
    "LLM_MODEL",
    "qwen2.5-1.5b-instruct"
)

LLM_API_KEY = os.getenv(
    "LLM_API_KEY",
    "lm-studio"
)

LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "60"))

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./suggestions.db"
)
