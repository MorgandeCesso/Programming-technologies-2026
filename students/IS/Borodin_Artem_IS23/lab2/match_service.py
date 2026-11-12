import os
from dotenv import load_dotenv
import psycopg

load_dotenv()


def normalize_code(code):
    if code is None:
        return None
    if not isinstance(code, str):
        return None
    code = code.strip().upper()
    if code == "":
        return None
    return code


def match_service(code):
    code = normalize_code(code)
    if code is None:
        return None, "not_provided", None

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM services WHERE UPPER(TRIM(code)) = %s",
                (code,),
            )
            row = cur.fetchone()

    if row is None:
        return None, "not_found", code
    return row[0], "matched", code


if __name__ == "__main__":
    for code in ("SV-012", " sv-012 ", "SV-999", None, ""):
        service_id, status, saved_code = match_service(code)
        print(repr(code), "->", service_id, status, saved_code)