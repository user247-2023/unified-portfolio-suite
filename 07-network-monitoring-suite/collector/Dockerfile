# Collector image. Runs the Prometheus exporter as a non-root user.
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd --create-home --uid 10001 appuser
USER appuser
CMD ["python", "collector.py"]
