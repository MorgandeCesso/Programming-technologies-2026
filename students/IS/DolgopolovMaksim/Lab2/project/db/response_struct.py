import sqlite3


def row_to_response(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "date": row["date"],
        "input_text": row["input_text"],
        "category": row["category"],
        "summary": row["summary"],
        "book_code": row["book_code"],
        "reader_card": row["reader_card"],
        "requested_period": row["requested_period"],
        "details": row["details"],
        "edition_id": row["edition_id"],
        "result_status": row["result_status"],
    }