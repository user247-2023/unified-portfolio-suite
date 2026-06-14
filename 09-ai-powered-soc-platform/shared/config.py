"""Environment-driven configuration for the SOC platform.

Purpose: Centralize every tunable in one place, read from environment variables
only. No secret or threshold is hardcoded in business logic.

Security trade-off: `INGEST_API_KEY` has no default — if it is unset the
ingestion service refuses authenticated routes (fail-closed) rather than running
open. Detection thresholds have safe defaults but are overridable per deployment.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class Settings:
    # --- Ingestion auth (no default: must be provided to enable ingest) ------
    ingest_api_key: str | None = os.environ.get("INGEST_API_KEY")

    # --- Correlation thresholds ---------------------------------------------
    correlation_window_seconds: int = _int("CORRELATION_WINDOW_SECONDS", 300)
    brute_force_threshold: int = _int("BRUTE_FORCE_THRESHOLD", 5)
    port_scan_threshold: int = _int("PORT_SCAN_THRESHOLD", 15)

    # --- Triage --------------------------------------------------------------
    # Risk score (0-100) at/above which an incident is auto-escalated to P1.
    auto_escalate_score: int = _int("AUTO_ESCALATE_SCORE", 80)

    # --- Service wiring ------------------------------------------------------
    bind_host: str = os.environ.get("BIND_HOST", "0.0.0.0")
    bind_port: int = _int("BIND_PORT", 8000)


settings = Settings()
