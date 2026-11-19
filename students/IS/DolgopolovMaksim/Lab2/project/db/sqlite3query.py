import sqlite3
import os

conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)), './library.db'))
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        input_text TEXT NOT NULL,
        category TEXT NOT NULL,
        summary TEXT NOT NULL,
        book_code TEXT,
        reader_card TEXT,
        requested_period TEXT,
        result_status TEXT NOT NULL,
        edition_id INTEGER REFERENCES editions(id),
        details TEXT,
        CHECK (result_status IN ('matched', 'not_found', 'not_provided'))
    );
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS editions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        publisher TEXT NOT NULL,
        book_code TEXT NOT NULL UNIQUE,
        type TEXT NOT NULL,
        target_audience TEXT NOT NULL
    );
''')
cursor.execute('''
    CREATE UNIQUE INDEX IF NOT EXISTS editions_book_code_normalized
    ON editions (UPPER(TRIM(book_code)));
''')

cursor.execute('''
    INSERT OR IGNORE INTO editions (name, publisher, book_code, type, target_audience) VALUES
    ("Учимся читать", "Читай-ка", "A-121", "Детская литература", "Дети"),
    ("Солнечная система: простым языком", "Умная сова", "B-245", "Научно-популярная литература", "Подростки"),
    ("Крепёж: всё о нём и многое другое", "Ключ", "C-572", "Техническая литература", "Взрослые"),
    ("Всевозможные силы и не только", "Гравитация", "D-895", "Учебное пособие по физике", "Взрослые"),
    ("Инцидент в городе Бяков", "Загадка", "E-736", "Детективная литература", "Взрослые")
''')

conn.commit()
conn.close()