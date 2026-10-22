from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("FIRST_API_KEY")
api_key2 = os.getenv("SECOND_API_KEY")
base_url = os.getenv("BASE_URL")

client = OpenAI(
    api_key=api_key,
    base_url=base_url,
)

def get_response(text: str, client: OpenAI):
    response = client.responses.create(model="openrouter/free", input=text)
    return response

if __name__ == "__main__":
    print("Введите ваш вопрос (или 'exit' для выхода):")
    while True:
        question = input("Вы: ")
        if question.lower() == "exit":
            print("Завершение программы.")
            break
        answer = get_response(question, client)
        print("AI:", answer.output_text)