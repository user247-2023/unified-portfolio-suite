"""Log ingestion service (FastAPI).

Purpose: HTTP edge of the SOC platform. Accepts batches of raw log events,
authenticates the producer, runs them through the detection pipeline, and
exposes the resulting alerts/incidents to the dashboard.

Security trade-offs:
 - API-key auth via the `X-API-Key` header, compared with `hmac.compare_digest`
   (constant-time) to avoid timing side channels. If `INGEST_API_KEY` is unset,
   authenticated routes return 503 (FAIL CLOSED) rather than running open.
 - Request body size is bounded and each batch is capped (anti-DoS).
 - Input is validated by Pydantic models before reaching the pipeline.

Run locally (from the project root, so `shared`/`services` are importable):
    uvicorn services.ingestion.app.main:app --reload
"""
from __future__ import annotations

import hmac
import os

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from shared.config import settings

from .pipeline import Pipeline

app = FastAPI(title="AI-Powered SOC — Ingestion", version="0.1.0")
pipeline = Pipeline()

# The dashboard is a separate origin, so the browser needs CORS to call us.
# Allowed origins are configurable; default to the local dashboard ports.
_cors_origins = os.environ.get(
    "CORS_ORIGINS", "http://localhost:5173,http://localhost:8080"
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins if o.strip()],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

MAX_BATCH = 1000


class IngestRequest(BaseModel):
    source: str = Field(min_length=1, max_length=64)
    events: list[dict] = Field(min_length=1, max_length=MAX_BATCH)


def require_api_key(x_api_key: str = Header(default="")) -> None:
    """Fail-closed API-key auth dependency."""
    if not settings.ingest_api_key:
        # No key configured => refuse rather than accept everything.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ingest disabled: INGEST_API_KEY not configured",
        )
    if not hmac.compare_digest(x_api_key, settings.ingest_api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="invalid API key")


@app.get("/healthz")
def healthz() -> dict:
    """Unauthenticated liveness probe."""
    return {"status": "ok"}


@app.post("/ingest", dependencies=[Depends(require_api_key)])
def ingest(req: IngestRequest) -> dict:
    """Ingest a batch of raw events and return detection results."""
    return pipeline.process(req.source, req.events)


@app.get("/incidents", dependencies=[Depends(require_api_key)])
def list_incidents() -> dict:
    """Return triaged incidents, most urgent first."""
    from .pipeline import _incident_summary

    ordered = sorted(pipeline.incidents,
                     key=lambda i: (i.priority, -i.risk_score))
    return {"incidents": [_incident_summary(i) for i in ordered]}
