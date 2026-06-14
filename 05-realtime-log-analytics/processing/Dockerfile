# Stream processor image.
# Purpose: Run the Kafka->ClickHouse processor.
# Security note: runs as a non-root user; no secrets baked in (env_file at runtime).
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Defensive: drop root.
RUN useradd --create-home --uid 10001 appuser
USER appuser

CMD ["python", "processor.py"]
