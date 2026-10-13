FROM python:3.12-slim-bookworm
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps chromium
COPY . .
ENV DB_PATH=/data/painel.db
CMD gunicorn app:app --bind 0.0.0.0:${PORT:-8000} --workers 1 --threads 4 --timeout 180
