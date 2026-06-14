"""Monitoring core (pure stdlib, testable offline).

Purpose: The decision logic of the collector — turning a raw probe outcome into
a result, tracking rolling latency, and evaluating alert conditions — with no
dependency on prometheus_client or live sockets, so it is unit-testable.

Design: `collector.py` performs the socket I/O and metric export; it delegates
classification and alerting here. Keeping this layer pure makes the alerting
rules (the part most likely to change) trivial to test.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class ProbeResult:
    name: str
    host: str
    up: bool
    latency_s: float | None   # None when the target is down


@dataclass(frozen=True)
class AlertConfig:
    latency_warn_s: float = 0.5   # warn when a probe is slower than this


def classify(name: str, host: str, connected: bool,
             latency_s: float | None) -> ProbeResult:
    """Build a ProbeResult, enforcing the invariant that a down target has no
    latency (defensive: callers can't report 'up=False' with a latency)."""
    if not connected:
        return ProbeResult(name=name, host=host, up=False, latency_s=None)
    return ProbeResult(name=name, host=host, up=True, latency_s=latency_s)


class RollingLatency:
    """Fixed-window rolling latency tracker (for trend/averaging in dashboards)."""

    def __init__(self, window: int = 20) -> None:
        self._samples: deque[float] = deque(maxlen=window)

    def add(self, latency_s: float | None) -> None:
        if latency_s is not None:
            self._samples.append(latency_s)

    def average(self) -> float | None:
        return sum(self._samples) / len(self._samples) if self._samples else None

    def count(self) -> int:
        return len(self._samples)


def evaluate_alerts(result: ProbeResult, cfg: AlertConfig) -> list[str]:
    """Return alert strings for a probe result (empty if healthy)."""
    if not result.up:
        return [f"DOWN: {result.name} ({result.host}) is unreachable"]
    if result.latency_s is not None and result.latency_s > cfg.latency_warn_s:
        return [f"SLOW: {result.name} latency {result.latency_s * 1000:.0f}ms "
                f"exceeds {cfg.latency_warn_s * 1000:.0f}ms"]
    return []
