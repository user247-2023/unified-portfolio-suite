"""Correlation engine.

Purpose: Maintain a per-entity sliding window of recent events and run the
detection rules against it as new events arrive, emitting de-duplicated Alerts.

Design / trade-offs:
 - State is kept in-memory per entity with time-based eviction. This is simple,
   fast, and adequate for a single-node demo. A production deployment would back
   the window with a durable, shardable store (e.g. Redis/streams) so state
   survives restarts and scales horizontally — called out here intentionally.
 - Alert de-duplication: a (rule, entity) pair won't re-fire until its window
   has rolled over, preventing alert storms from a sustained attack while still
   re-alerting if the behavior recurs later.
 - Pure rule functions + explicit window make the whole engine deterministic and
   unit-testable without any infrastructure.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from shared.models import Alert, Event

from .rules import ALL_RULES, RuleConfig


class CorrelationEngine:
    def __init__(self, window_seconds: int = 300,
                 rule_config: RuleConfig | None = None) -> None:
        self._window = timedelta(seconds=window_seconds)
        self._cfg = rule_config or RuleConfig()
        self._events: dict[str, list[Event]] = defaultdict(list)
        # Tracks (rule, entity) -> time last alerted, for de-duplication.
        self._last_alert: dict[tuple[str, str], datetime] = {}

    def _evict(self, entity: str, now: datetime) -> None:
        cutoff = now - self._window
        self._events[entity] = [
            e for e in self._events[entity] if e.timestamp >= cutoff
        ]

    def ingest(self, event: Event) -> list[Alert]:
        """Add an event and return any alerts it triggers."""
        entity = event.entity()
        now = datetime.now(timezone.utc)
        self._events[entity].append(event)
        self._evict(entity, now)

        alerts: list[Alert] = []
        window = self._events[entity]
        for rule in ALL_RULES:
            alert = rule(entity, window, self._cfg)
            if alert is None:
                continue
            key = (alert.rule, entity)
            last = self._last_alert.get(key)
            # Suppress duplicate alerts for the same rule+entity within the window.
            if last is not None and now - last < self._window:
                continue
            self._last_alert[key] = now
            alerts.append(alert)
        return alerts

    def window_size(self, entity: str) -> int:
        """Current number of retained events for an entity (diagnostics/tests)."""
        return len(self._events.get(entity, []))
