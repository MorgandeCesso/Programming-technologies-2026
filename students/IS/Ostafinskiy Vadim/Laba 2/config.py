
import os
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("LM_STUDIO_MODEL", "qwen3.5-9b")
BASE_URL = os.getenv("LM_STUDIO_BASE_URL")
API_KEY = os.getenv("LM_STUDIO_API_KEY")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "60"))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./workshop.db")
