"""Automated incident triage.

Purpose: Take correlated alerts, group related ones into an Incident, score its
risk, assign a priority, and attach recommended response actions + a transparent
rationale. This is the "automated incident triage logic" — it turns raw
detections into a prioritized, actionable queue for analysts.

Trade-offs:
 - Grouping is by shared entity within a batch — alerts about the same IP/user
   become one incident. This keeps related noise together without overreaching;
   cross-entity campaign correlation is a deliberate future step.
 - Priority is derived from the explainable risk score (not a black box), and
   auto-escalation to P1 is threshold-driven via config so it's auditable.
 - Triage never auto-executes remediation; it recommends. (See playbooks.py.)
"""
from __future__ import annotations

from collections import defaultdict

from shared.models import Alert, Incident, Priority

from .playbooks import actions_for_alerts
from .scoring import score_incident


def _priority_for(score: int, auto_escalate_score: int) -> Priority:
    if score >= auto_escalate_score:
        return Priority.P1
    if score >= 60:
        return Priority.P2
    if score >= 40:
        return Priority.P3
    return Priority.P4


def _group_by_entity(alerts: list[Alert]) -> dict[str, list[Alert]]:
    groups: dict[str, list[Alert]] = defaultdict(list)
    for alert in alerts:
        groups[alert.entity].append(alert)
    return groups


def triage(alerts: list[Alert], auto_escalate_score: int = 80) -> list[Incident]:
    """Convert a batch of alerts into prioritized incidents."""
    incidents: list[Incident] = []
    for entity, grouped in _group_by_entity(alerts).items():
        score, rationale = score_incident(grouped)
        priority = _priority_for(score, auto_escalate_score)
        rules = {a.rule for a in grouped}
        incident = Incident(
            alerts=grouped,
            risk_score=score,
            priority=priority,
            recommended_actions=actions_for_alerts(rules),
            rationale=[f"entity={entity}", *rationale,
                       f"priority={priority.name} "
                       f"(auto-escalate at {auto_escalate_score})"],
        )
        incidents.append(incident)

    # Most urgent first: P1 before P4, then higher score first.
    incidents.sort(key=lambda i: (i.priority, -i.risk_score))
    return incidents
