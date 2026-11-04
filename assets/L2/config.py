import os

from dotenv import load_dotenv

load_dotenv()

MODEL_TOKEN = os.getenv("MODEL_TOKEN")
BASE_URL = os.getenv("BASE_URL")
MODEL = os.getenv("MODEL")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://lab:lab@localhost:5432/vivarium",
)
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "60"))
