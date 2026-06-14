"""Log normalizer.

Purpose: Convert heterogeneous raw log payloads (SSH auth, firewall, generic
JSON app logs) into the platform's canonical `Event`. Correlation/triage then
operate on ONE schema, regardless of source.

Security trade-offs:
 - Every field is read defensively with bounds (string truncation) so a hostile
   producer can't blow up memory or smuggle oversized values downstream.
 - Unknown sources fall through to a generic mapping rather than being dropped —
   we never silently lose telemetry.
"""
from __future__ import annotations

from datetime import datetime, timezone

from shared.models import Event, Severity

_MAX = 1024  # max length we keep for any single free-text field


def _s(value: object, limit: int = _MAX) -> str:
    """Coerce to a bounded string (defensive against oversized/None input)."""
    if value is None:
        return ""
    return str(value)[:limit]


def _parse_ts(value: object) -> datetime:
    """Best-effort timestamp parse; defaults to now (UTC) on anything odd."""
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            pass
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def _normalize_sshd(raw: dict) -> Event:
    """Map an SSH daemon auth record. `outcome` in {failure, success}."""
    outcome = _s(raw.get("outcome", "failure"), 16).lower()
    event_type = "auth_success" if outcome == "success" else "auth_failure"
    return Event(
        source="sshd",
        event_type=event_type,
        host=_s(raw.get("host"), 255),
        user=_s(raw.get("user"), 255) or None,
        src_ip=_s(raw.get("src_ip"), 64) or None,
        severity=Severity.LOW if event_type == "auth_failure" else Severity.INFO,
        message=_s(raw.get("message")),
        timestamp=_parse_ts(raw.get("timestamp")),
        attributes={"port": _s(raw.get("port"), 8)},
    )


def _normalize_firewall(raw: dict) -> Event:
    action = _s(raw.get("action", "deny"), 16).lower()
    return Event(
        source="firewall",
        event_type="connection_denied" if action == "deny" else "connection_allowed",
        host=_s(raw.get("device"), 255),
        src_ip=_s(raw.get("src_ip"), 64) or None,
        dest_ip=_s(raw.get("dest_ip"), 64) or None,
        severity=Severity.LOW if action == "deny" else Severity.INFO,
        message=_s(raw.get("message")),
        timestamp=_parse_ts(raw.get("timestamp")),
        attributes={"dport": _s(raw.get("dest_port"), 8),
                    "proto": _s(raw.get("proto"), 8)},
    )


def _normalize_generic(raw: dict) -> Event:
    return Event(
        source=_s(raw.get("source", "app"), 64),
        event_type=_s(raw.get("event_type", "log"), 64),
        host=_s(raw.get("host"), 255),
        user=_s(raw.get("user"), 255) or None,
        src_ip=_s(raw.get("src_ip"), 64) or None,
        dest_ip=_s(raw.get("dest_ip"), 64) or None,
        severity=Severity.coerce(raw.get("severity", "INFO")),
        message=_s(raw.get("message")),
        timestamp=_parse_ts(raw.get("timestamp")),
        attributes=dict(raw.get("attributes", {})) if isinstance(raw.get("attributes"), dict) else {},
    )


_DISPATCH = {
    "sshd": _normalize_sshd,
    "firewall": _normalize_firewall,
}


def normalize(source: str, raw: dict) -> Event:
    """Normalize a raw payload from `source` into a canonical Event."""
    if not isinstance(raw, dict):
        raise ValueError("raw payload must be a JSON object")
    handler = _DISPATCH.get((source or "").lower(), _normalize_generic)
    return handler(raw)
