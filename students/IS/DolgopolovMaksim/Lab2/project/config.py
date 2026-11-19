import os
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = "gemma-4-e4b-it"
BASE_URL = "http://127.0.0.1:1234/v1"
API_KEY = "sk-lm-88vzTOWU:y8AT6lYDX9zjFZsiQMNF"
DATABASE_PATH = "./db/library.db"
TEMPERATURE = 0.5
LLM_TIMEOUT = 60.0