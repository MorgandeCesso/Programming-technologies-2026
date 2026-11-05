import os
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:7000/v1",
    api_key=os.environ["LMSTUDIO_API_KEY"],
)

for m in client.models.list().data:
    print(m.id)