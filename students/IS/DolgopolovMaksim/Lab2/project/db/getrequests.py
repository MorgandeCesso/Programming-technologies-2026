import sqlite3
import os

conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)), './library.db'))
cursor = conn.cursor()

cursor.execute("SELECT * FROM requests")
requests = cursor.fetchall()
cursor.close()

print(requests)