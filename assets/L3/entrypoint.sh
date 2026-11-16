#!/bin/sh
set -eu

echo "Индексация документов в Qdrant"
python -m vector_db.embedder

echo "Очистка docs/temp"
rm -rf docs/temp

echo "Запуск API"
exec uvicorn main:app --host 0.0.0.0 --port 8000
