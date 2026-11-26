import sqlite3
from pathlib import Path

from app import config
from app.errors import SqlError

SCHEMA = """
CREATE TABLE devices (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    location TEXT NOT NULL,
    ip TEXT NOT NULL
);
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    device_code TEXT NOT NULL REFERENCES devices(code),
    event_code TEXT NOT NULL,
    severity TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    cleared_at TEXT
);
CREATE TABLE tickets (
    number TEXT PRIMARY KEY,
    device_code TEXT NOT NULL REFERENCES devices(code),
    event_code TEXT NOT NULL,
    priority TEXT NOT NULL,
    status TEXT NOT NULL,
    opened_at TEXT NOT NULL,
    resolved_at TEXT,
    closed_at TEXT,
    failure_cause TEXT
);
"""


def create_database(path: Path, devices: list[tuple], events: list[tuple], tickets: list[tuple]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    with sqlite3.connect(path) as connection:
        connection.executescript(SCHEMA)
        connection.executemany("INSERT INTO devices VALUES (?, ?, ?, ?)", devices)
        connection.executemany(
            "INSERT INTO events (device_code, event_code, severity, occurred_at, cleared_at) VALUES (?, ?, ?, ?, ?)",
            events,
        )
        connection.executemany("INSERT INTO tickets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", tickets)
    connection.close()


def execute_readonly(statement: str, max_rows: int, path: Path | None = None) -> list[dict]:
    path = path or config.SQL_PATH
    if not path.exists():
        raise SqlError("База событий не найдена, запустите seed_db.py")
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        cursor = connection.execute(statement)
        columns = [item[0] for item in cursor.description or []]
        return [dict(zip(columns, row)) for row in cursor.fetchmany(max_rows)]
    except sqlite3.Error as error:
        raise SqlError(f"Ошибка выполнения запроса: {error}")
    finally:
        connection.close()
