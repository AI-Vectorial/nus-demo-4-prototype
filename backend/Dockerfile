FROM python:3.12-slim

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

# The policy corpus, read-only: ingestion indexes it on first boot and the
# refusal names its owners. Never copied into the database (REQ-B5).
COPY corpus/ ./corpus/

# Railway supplies $PORT
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
