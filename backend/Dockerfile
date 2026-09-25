FROM python:3.12-slim

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

# The corpus is read at runtime -- by ingestion, and by /corpus on every
# request (REQ-B5, so there is no second copy in the database to fall out of
# step). Without this line both work locally and fail only once deployed,
# which is the worst way to find out.
COPY corpus/ ./corpus/

# Railway supplies $PORT
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
