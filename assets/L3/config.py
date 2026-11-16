import os

from dotenv import load_dotenv

load_dotenv()

MODEL_TOKEN = os.getenv("MODEL_TOKEN")
BASE_URL = os.getenv("BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "120"))
