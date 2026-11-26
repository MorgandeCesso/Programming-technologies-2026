import os
from dotenv import load_dotenv

load_dotenv()

MODEL_TOKEN = os.getenv("LM_STUDIO_API_KEY", "")
BASE_URL = os.getenv("BASE_URL", "http://localhost:7000/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen3.5-9b")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "60"))
