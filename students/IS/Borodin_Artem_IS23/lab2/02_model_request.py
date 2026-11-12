import json
import os
import time
import importlib.util
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

spec = importlib.util.spec_from_file_location("schema", "01_pydantic_parse.py")
schema = importlib.util.module_from_spec(spec)
spec.loader.exec_module(schema)

client = OpenAI(
    base_url=os.environ["LMSTUDIO_BASE_URL"],
    api_key=os.environ["LMSTUDIO_API_KEY"],
    timeout=60,
)

instruction = """
Верни только JSON с шестью полями:
category, summary, service_code, item_description, deadline_text, details.
category - одно из значений: manufacture, repair, customization, other.
manufacture - изготовление, repair - ремонт, customization - гравировка или персонализация.
Если категория неясна, поставь other.
summary - краткое содержание, непустая строка.
service_code - код услуги из текста или null. Не выдумывай код и не подбирай его по названию.
item_description - изделие или null.
deadline_text - срок так, как он написан, или null. Даты не пересчитывай.
details - важная деталь, которой нет в остальных полях, или null.
Не придумывай отсутствующие сведения. Не пиши SQL. Других полей не добавляй.
"""

message = 'Хочу заказать гравировку по услуге SV-012 на металлической фляге к 20 ноября. Текст: "За новые открытия!"'

start = time.perf_counter()
response = client.chat.completions.create(
    model=os.environ["LMSTUDIO_MODEL"],
    temperature=0,
    messages=[
        {"role": "system", "content": instruction},
        {"role": "user", "content": message},
    ],
)
seconds = time.perf_counter() - start
usage = response.usage

print(f"Входные токены: {usage.prompt_tokens}")
print(f"Токены ответа: {usage.completion_tokens}")
print(f"Всего токенов: {usage.total_tokens}")
print(f"Время: {seconds:.1f} с")
print(f"Токенов в секунду: {usage.completion_tokens / seconds:.1f}")

text = response.choices[0].message.content.strip()
if text.startswith("```"):
    lines = text.splitlines()[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    text = "\n".join(lines)

print(text)
order = schema.check_order(json.loads(text))
print(order)