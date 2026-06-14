"""Detection rules for the correlation engine.

Purpose: Each rule inspects the recent event window for a single entity (an IP
or user) and optionally emits an Alert. Rules are pure functions of their input
window — no I/O — which makes them trivially unit-testable and safe to run in
any order.

Security trade-off: thresholds come from config (no magic numbers in logic), so
detection sensitivity is tunable per environment without code changes. Rules
favor explainability (clear titles/descriptions) over opaque scoring so analysts
can trust and tune them.
"""
from __future__ import annotations

from typing import Callable

from shared.models import Alert, Event, Severity

# A rule: given (entity, window, config) -> an Alert or None.
Rule = Callable[[str, list[Event], "RuleConfig"], "Alert | None"]


class RuleConfig:
    """Thresholds passed to rules. Mirrors shared.config.Settings but kept as a
    plain object so rules don't depend on environment at import time."""

    def __init__(self, brute_force_threshold: int = 5,
                 port_scan_threshold: int = 15) -> None:
        self.brute_force_threshold = brute_force_threshold
        self.port_scan_threshold = port_scan_threshold


def brute_force_rule(entity: str, window: list[Event], cfg: RuleConfig) -> Alert | None:
    """N+ auth failures from one entity within the window => brute force."""
    failures = [e for e in window if e.event_type == "auth_failure"]
    if len(failures) >= cfg.brute_force_threshold:
        return Alert(
            rule="brute_force",
            title=f"Possible brute-force from {entity}",
            severity=Severity.HIGH,
            entity=entity,
            description=(f"{len(failures)} authentication failures within the "
                         f"correlation window (threshold {cfg.brute_force_threshold})."),
            events=failures,
        )
    return None


def success_after_failures_rule(entity: str, window: list[Event],
                                cfg: RuleConfig) -> Alert | None:
    """Auth success preceded by many failures => likely SUCCESSFUL brute force.
    This is higher severity than failures alone (the attacker may be in)."""
    ordered = sorted(window, key=lambda e: e.timestamp)
    failures_before = 0
    for e in ordered:
        if e.event_type == "auth_failure":
            failures_before += 1
        elif e.event_type == "auth_success":
            if failures_before >= cfg.brute_force_threshold:
                return Alert(
                    rule="successful_brute_force",
                    title=f"Successful login after {failures_before} failures: {entity}",
                    severity=Severity.CRITICAL,
                    entity=entity,
                    description=("A successful authentication followed a burst of "
                                 "failures from the same entity — possible account "
                                 "compromise."),
                    events=ordered,
                )
            failures_before = 0  # reset after a success
    return None


def port_scan_rule(entity: str, window: list[Event], cfg: RuleConfig) -> Alert | None:
    """Many distinct denied destination ports from one source => port scan."""
    ports = {
        e.attributes.get("dport")
        for e in window
        if e.event_type == "connection_denied" and e.attributes.get("dport")
    }
    if len(ports) >= cfg.port_scan_threshold:
        return Alert(
            rule="port_scan",
            title=f"Possible port scan from {entity}",
            severity=Severity.HIGH,
            entity=entity,
            description=(f"{len(ports)} distinct destination ports denied within "
                         f"the window (threshold {cfg.port_scan_threshold})."),
            events=[e for e in window if e.event_type == "connection_denied"],
        )
    return None


# Registry the engine iterates. Add a rule here to enable it.
ALL_RULES: list[Rule] = [
    success_after_failures_rule,   # check the worst case first
    brute_force_rule,
    port_scan_rule,
]
