"""End-to-end detection pipeline.

Purpose: Compose the stages — normalize -> enrich -> correlate -> triage — into
a single callable the ingestion API (and tests) can drive. Holds the
correlation engine state and an in-memory incident store for the demo.

Trade-off: in-memory state is fine for a single-node demo and for deterministic
tests. Production would persist incidents to a datastore and run correlation as
a scalable consumer; this class is the seam where that swap happens.
"""
from __future__ import annotations

from shared.config import settings
from shared.models import Alert, Incident

from services.correlation.app.engine import CorrelationEngine
from services.correlation.app.rules import RuleConfig
from services.triage.app.triage import triage

from .enrichment import enrich
from .normalizer import normalize


class Pipeline:
    def __init__(self) -> None:
        self._engine = CorrelationEngine(
            window_seconds=settings.correlation_window_seconds,
            rule_config=RuleConfig(
                brute_force_threshold=settings.brute_force_threshold,
                port_scan_threshold=settings.port_scan_threshold,
            ),
        )
        self.incidents: list[Incident] = []
        self.recent_alerts: list[Alert] = []

    def process(self, source: str, raw_events: list[dict]) -> dict:
        """Run a batch of raw events through the full pipeline."""
        alerts: list[Alert] = []
        ingested = 0
        for raw in raw_events:
            event = enrich(normalize(source, raw))
            ingested += 1
            alerts.extend(self._engine.ingest(event))

        new_incidents = triage(alerts, settings.auto_escalate_score) if alerts else []
        self.recent_alerts.extend(alerts)
        self.recent_alerts = self.recent_alerts[-500:]   # bound memory
        self.incidents.extend(new_incidents)
        self.incidents = self.incidents[-500:]

        return {
            "events_ingested": ingested,
            "alerts_raised": len(alerts),
            "incidents_created": len(new_incidents),
            "incidents": [_incident_summary(i) for i in new_incidents],
        }


def _incident_summary(inc: Incident) -> dict:
    """Compact, JSON-safe view of an incident for API responses."""
    return {
        "id": inc.id,
        "priority": inc.priority.name,
        "risk_score": inc.risk_score,
        "entities": sorted(inc.entities()),
        "alert_rules": sorted({a.rule for a in inc.alerts}),
        "recommended_actions": inc.recommended_actions,
        "rationale": inc.rationale,
    }
