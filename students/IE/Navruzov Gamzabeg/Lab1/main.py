import os

os.environ["NO_PROXY"] = "127.0.0.1,localhost"
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key=os.getenv("LMSTUDIO_API_KEY"),
)

MODEL = "qwen2.5-3b-instruct"
#MODEL = "llama-3.2-3b-instruct"# для второй проверки поменять на "llama-3.2-3b-instruct"

models = client.models.list()
print("Модели:")
for model in models.data:
    print(f"  - {model.id}")

response = client.responses.create(
    model=MODEL,
    input="Моё имя Гамзабег",
)
print()
print(response.output_text)
