from datetime import date

from app import config
from app.db import sql_store
from app.errors import LLMInvalidResponse, SqlError
from app.logic import llm

SQL_PROMPT = """
Переведи вопрос в один запрос SELECT для SQLite по схеме базы мониторинга сети.

devices(code, name, location, ip)
Коды устройств: SW-CORE-01, SW-CORE-02, RT-EDGE-01, FW-01, SW-ACC-11, SW-ACC-12, SW-ACC-21, SW-ACC-22, SRV-MON-01.

events(id, device_code, event_code, severity, occurred_at, cleared_at)
События мониторинга. event_code: L101, L102, L201, P301, T401, C501, S601, B701, F801.
Допустимые severity: «Авария», «Предупреждение».
cleared_at = NULL, если событие ещё активно.

tickets(number, device_code, event_code, priority, status, opened_at, resolved_at, closed_at, failure_cause)
Заявки на устранение. priority: P1, P2, P3, P4.
Допустимые status: «Зарегистрировано», «В работе», «Решено», «Закрыто».
Допустимые failure_cause: «Физический уровень», «Питание», «Перегрев», «Конфигурация», «Внешний провайдер», «Не подтвердилось», NULL у незакрытых заявок.

Даты хранятся текстом в формате 'YYYY-MM-DD HH:MM'. Отбор за месяц: occurred_at LIKE '2026-11-%'. Отбор за период: occurred_at >= '2026-11-01' AND occurred_at < '2026-12-01'.
Сегодня {today}.

Таблиц и столбцов вне схемы нет. INSERT, UPDATE, DELETE и другие изменения не пиши.
Верни только текст запроса, без пояснений и без markdown.
""".strip()


def validate_select(sql: str) -> str:
    statement = " ".join(sql.split()).rstrip(";").strip()
    if not statement.lower().startswith("select") or ";" in statement:
        raise SqlError("Разрешён один запрос SELECT")
    return statement


def generate_sql(question: str, user_message: str | None = None) -> str:
    request = question
    if user_message and user_message.strip() != question.strip():
        request = f"Реплика пользователя: {user_message}\nЧто нужно найти в базе: {question}"
    message = llm.chat(
        [
            {"role": "system", "content": SQL_PROMPT.format(today=date.today().isoformat())},
            {"role": "user", "content": request},
        ]
    )
    sql = llm.strip_fences(message.content or "")
    if not sql:
        raise LLMInvalidResponse("Модель не вернула SQL-запрос")
    return sql


def ask_database(question: str, user_message: str | None = None) -> dict:
    statement = validate_select(generate_sql(question, user_message))
    rows = sql_store.execute_readonly(statement, config.MAX_SQL_ROWS)
    return {"sql": statement, "rows": rows}
