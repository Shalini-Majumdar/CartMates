FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini ./
COPY ./app ./app

EXPOSE 8000

# Alembic runs from /app (where alembic.ini lives); the app's imports are
# rooted at the package directory, so uvicorn runs from /app/app.
# The seed only inserts into an empty products table, so it is safe on every
# start. Hosts such as Render pass the port in $PORT; 8000 is the local default.
CMD ["sh", "-c", "alembic upgrade head && cd app && python seed_products.py && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
