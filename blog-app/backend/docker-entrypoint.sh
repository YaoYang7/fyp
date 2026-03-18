#!/bin/sh
set -e

echo "Initialising database tables..."
python -c "
from app.db import engine
from app import models
models.Base.metadata.create_all(bind=engine)
print('Database tables ready.')
"

exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 1
