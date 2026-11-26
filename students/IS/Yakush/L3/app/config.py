import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

SOURCE_DIR = ROOT / "docs" / "source"
TEMP_DIR = ROOT / "docs" / "temp"
QDRANT_DIR = ROOT / "qdrant"
COLLECTION = "docs"
SQL_PATH = Path(os.getenv("SQL_PATH", str(ROOT / "data" / "network.db")))

EMBED_MODEL = "BAAI/bge-m3"
TOKENIZER_NAME = "BAAI/bge-m3"
CHUNK_SIZE = 600
CHUNK_OVERLAP = 60
SEARCH_LIMIT = 3
MAX_SQL_ROWS = 50
MAX_TOOL_ROUNDS = 3

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://127.0.0.1:7000/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen3.5-4b")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "300"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "8000"))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))
