import os
from dotenv import load_dotenv
import psycopg

load_dotenv()

services = [
    ("SV-012", "Гравировка"),
    ("SV-003", "Изготовление таблички"),
    ("SV-018", "Ремонт замка"),
    ("SV-025", "Заточка инструмента"),
    ("SV-031", "Покраска изделия"),
]

with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS services (
                id SERIAL PRIMARY KEY,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL
            )
        """)
        for code, name in services:
            cur.execute(
                """
                INSERT INTO services (code, name)
                VALUES (%s, %s)
                ON CONFLICT (code) DO NOTHING
                """,
                (code, name),
            )
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                message TEXT NOT NULL,
                category TEXT NOT NULL,
                summary TEXT NOT NULL,
                service_code TEXT,
                item_description TEXT,
                deadline_text TEXT,
                details TEXT,
                service_id INTEGER REFERENCES services(id),
                match_status TEXT NOT NULL
            )
        """)
    conn.commit()

print("Справочник готов")