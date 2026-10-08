FROM python:3.12-slim

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
# The corpus is read at runtime too: by ingest, the corpus browser and the
# refusal's directory of policy owners (REQ-B5).
COPY corpus/ ./corpus/

# Railway supplies $PORT
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
