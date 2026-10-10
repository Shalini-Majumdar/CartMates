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
CMD ["sh", "-c", "alembic upgrade head && cd app && uvicorn main:app --host 0.0.0.0 --port 8000"]
