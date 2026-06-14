"""Explainable risk scoring for incident triage.

Purpose: Turn a set of correlated alerts into a single 0-100 risk score PLUS a
human-readable rationale for every point added. Analysts (and auditors) can see
exactly why an incident scored the way it did.

Design choice: a transparent, weighted heuristic instead of an opaque ML model.
In a SOC, explainability and tunability matter more than a marginal accuracy
gain — a score nobody understands is a score nobody trusts. The weights live in
one table so they can be tuned (or, later, learned) without touching the logic.

Defensive note: the score is always clamped to [0, 100]; new contributing
factors can only add bounded amounts, so no single signal can dominate
unexpectedly.
"""
from __future__ import annotations

from shared.models import Alert, Severity

# Base contribution from the most severe alert in the incident.
_SEVERITY_BASE = {
    Severity.CRITICAL: 50,
    Severity.HIGH: 35,
    Severity.MEDIUM: 20,
    Severity.LOW: 10,
    Severity.INFO: 0,
}

_PER_EXTRA_ALERT = 5          # each alert beyond the first
_EXTRA_ALERT_CAP = 20         # ...capped, so volume can't dominate severity
_EXTERNAL_SOURCE = 15         # an external IP is riskier than an internal one
_SENSITIVE_ACCOUNT = 15       # root/admin/service accounts
_MULTI_RULE = 10              # multiple distinct detections corroborate each other


def score_incident(alerts: list[Alert]) -> tuple[int, list[str]]:
    """Return (risk_score 0-100, rationale lines)."""
    if not alerts:
        return 0, ["No alerts: nothing to score."]

    rationale: list[str] = []
    max_sev = max(a.severity for a in alerts)
    score = _SEVERITY_BASE[max_sev]
    rationale.append(f"+{score} base from highest severity ({max_sev.name}).")

    extra = min((len(alerts) - 1) * _PER_EXTRA_ALERT, _EXTRA_ALERT_CAP)
    if extra:
        score += extra
        rationale.append(f"+{extra} for {len(alerts)} correlated alerts.")

    # Any event sourced from an external IP?
    if _any_external(alerts):
        score += _EXTERNAL_SOURCE
        rationale.append(f"+{_EXTERNAL_SOURCE} external source IP involved.")

    if _any_sensitive_account(alerts):
        score += _SENSITIVE_ACCOUNT
        rationale.append(f"+{_SENSITIVE_ACCOUNT} sensitive account targeted.")

    distinct_rules = {a.rule for a in alerts}
    if len(distinct_rules) > 1:
        score += _MULTI_RULE
        rationale.append(
            f"+{_MULTI_RULE} multiple distinct detections "
            f"({', '.join(sorted(distinct_rules))}).")

    score = max(0, min(100, score))   # clamp (defensive)
    rationale.append(f"= final risk score {score}/100.")
    return score, rationale


def _any_external(alerts: list[Alert]) -> bool:
    return any(
        e.attributes.get("src_scope") == "external"
        for a in alerts for e in a.events
    )


def _any_sensitive_account(alerts: list[Alert]) -> bool:
    return any(
        e.attributes.get("sensitive_account") == "true"
        for a in alerts for e in a.events
    )
