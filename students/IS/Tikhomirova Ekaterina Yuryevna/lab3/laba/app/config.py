import os
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

LM_BASE_URL = os.getenv(
    "LM_BASE_URL", "http://127.0.0.1:1234/v1"
).rstrip("/")
LM_API_KEY = os.getenv("LM_API_KEY", "lm-studio")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen3.5-4b")
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "text-embedding-bge-m3"
)
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "120"))

SOURCE_DIR = ROOT / "docs" / "source"
TEMP_DIR = ROOT / "docs" / "temp"
QDRANT_DIR = ROOT / "qdrant"
COLLECTION = "telemetry_docs"