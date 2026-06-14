"""Canonical domain models for the SOC platform.

Purpose: Define the single, normalized representation of a security Event, a
detection Alert, and a triaged Incident that every service shares. Using one
canonical schema (rather than passing provider-specific log shapes around) is
what lets correlation and triage stay simple and source-agnostic.

Design choice: plain `dataclasses` (stdlib) instead of Pydantic so this module
has ZERO third-party dependencies and can be unit-tested anywhere. Validation
that matters for security (e.g. clamping, enum coercion) is done explicitly.
"""
from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


class Severity(enum.IntEnum):
    """Ordered so code can threshold/compare numerically."""

    INFO = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    @classmethod
    def coerce(cls, value: object) -> "Severity":
        """Map arbitrary inputs (ints, names, syslog levels) to a Severity.
        Defensive: unknown values fail SAFE toward MEDIUM rather than being
        dropped or trusted as INFO."""
        if isinstance(value, Severity):
            return value
        if isinstance(value, int):
            return cls(max(0, min(4, value)))
        if isinstance(value, str):
            name = value.strip().upper()
            if name in cls.__members__:
                return cls[name]
        return cls.MEDIUM


class Priority(enum.IntEnum):
    """Incident priority. P1 is most urgent (note the inverted ordering vs int)."""

    P4 = 4
    P3 = 3
    P2 = 2
    P1 = 1


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


@dataclass
class Event:
    """A single normalized security event."""

    source: str                       # e.g. "sshd", "firewall", "cloudtrail"
    event_type: str                   # e.g. "auth_failure", "connection"
    host: str = ""
    user: str | None = None
    src_ip: str | None = None
    dest_ip: str | None = None
    severity: Severity = Severity.INFO
    message: str = ""
    timestamp: datetime = field(default_factory=_now)
    attributes: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: _new_id("evt"))

    def entity(self) -> str:
        """The primary entity this event concerns, used to group correlation.
        Prefers source IP, then user, then host — whatever identifies the actor."""
        return self.src_ip or self.user or self.host or "unknown"


@dataclass
class Alert:
    """A detection produced by the correlation engine from one or more events."""

    rule: str
    title: str
    severity: Severity
    entity: str
    description: str = ""
    events: list[Event] = field(default_factory=list)
    created_at: datetime = field(default_factory=_now)
    id: str = field(default_factory=lambda: _new_id("alrt"))


@dataclass
class Incident:
    """A triaged, prioritized grouping of alerts with recommended response."""

    alerts: list[Alert]
    risk_score: int = 0               # 0-100, computed by the triage scorer
    priority: Priority = Priority.P4
    status: str = "open"
    recommended_actions: list[str] = field(default_factory=list)
    rationale: list[str] = field(default_factory=list)   # explainability
    created_at: datetime = field(default_factory=_now)
    id: str = field(default_factory=lambda: _new_id("inc"))

    def entities(self) -> set[str]:
        return {a.entity for a in self.alerts}
