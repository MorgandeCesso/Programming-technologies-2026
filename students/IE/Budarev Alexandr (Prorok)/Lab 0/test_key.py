# вместо openai mistralai
from mistralai.client import Mistral
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("MISTRAL_API_KEY")

# гласс называется Mistral не OpenAI
client = Mistral(api_key=api_key)

# ОТЛИЧИЕ: вместо client.responses.create  client.chat.complete
# и передача списока messages а не просто input
response = client.chat.complete(
    model="ministral-8b-2512",
    messages=[
        {"role": "user", "content": "Скажи просто 'работает' и ничего больше"}
    ]
)

#достаём текст из response.choices[0].message.content
#(в OpenAI было response.output_text)
print(response.choices[0].message.content)