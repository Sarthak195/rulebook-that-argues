# Small CPU-only image. Build:  docker build -t rulebook .
# Run:    docker run --rm -p 8000:8000 --env-file .env rulebook
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 HF_HOME=/app/.hf
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.txt

COPY . .
# Download the embedding model and build the index at build time so the container starts fast.
RUN python scripts/ingest.py

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
