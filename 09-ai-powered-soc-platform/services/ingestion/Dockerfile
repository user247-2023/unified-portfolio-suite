# Ingestion service image.
# Purpose: Serve the FastAPI ingestion API. Build context is the PLATFORM ROOT
# (09-ai-powered-soc-platform) so `shared/` and the sibling service packages are
# importable — see docker-compose build.context.
# Security: runs as a non-root user; no secrets baked in (provided at runtime).
FROM python:3.12-slim

WORKDIR /app

# Install only the ingestion edge's deps; core logic is pure stdlib.
COPY services/ingestion/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the shared lib and the service packages needed at runtime.
COPY shared/ ./shared/
COPY services/ ./services/

RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000
CMD ["uvicorn", "services.ingestion.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
