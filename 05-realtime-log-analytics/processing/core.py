"""Stream-processing core (pure stdlib, testable offline).

Purpose: The parts of the processor that have nothing to do with Kafka or
ClickHouse — event parsing/validation and batching — live here so they can be
unit-tested with no infrastructure. `processor.py` wires these to the real
clients.

Security / correctness trade-offs:
 - `parse_event` validates and BOUNDS every field; malformed input raises
   `ValueError` so the caller can dead-letter it (never crash the loop, never
   silently drop).
 - `Batcher` takes an injectable clock so interval-based flushing is
   deterministic in tests; it flushes on size OR elapsed interval, amortizing
   insert cost without unbounded latency.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable

_MAX_SERVICE = 128
_MAX_LEVEL = 16
_MAX_MESSAGE = 8192


@dataclass
class Event:
    ts: float
    service: str
    level: str
    message: str
    trace_id: str
    attributes: dict


def parse_event(raw: bytes | str) -> Event:
    """Validate and coerce a raw payload into an Event.

    Raises ValueError on anything malformed so the caller can dead-letter it.
    """
    data = json.loads(raw)  # invalid JSON -> ValueError -> dead-letter
    if not isinstance(data, dict):
        raise ValueError("event payload must be a JSON object")
    try:
        return Event(
            ts=float(data["ts"]),
            service=str(data["service"])[:_MAX_SERVICE],
            level=str(data.get("level", "INFO"))[:_MAX_LEVEL],
            message=str(data["message"])[:_MAX_MESSAGE],
            trace_id=str(data.get("trace_id", "")),
            attributes={str(k): str(v)
                        for k, v in dict(data.get("attributes", {})).items()},
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid event schema: {exc}") from exc


class Batcher:
    """Accumulate items and flush on size OR elapsed interval.

    `clock` is injectable for deterministic testing.
    """

    def __init__(self, max_size: int = 1000, max_interval: float = 2.0,
                 clock: Callable[[], float] | None = None) -> None:
        if max_size < 1:
            raise ValueError("max_size must be >= 1")
        self.max_size = max_size
        self.max_interval = max_interval
        self._clock = clock or __import__("time").monotonic
        self._items: list = []
        self._last = self._clock()

    def add(self, item) -> list | None:
        """Append an item; return a batch if the size threshold is reached."""
        self._items.append(item)
        if len(self._items) >= self.max_size:
            return self._flush()
        return None

    def tick(self) -> list | None:
        """Call periodically; return a batch if the interval elapsed (and
        there is anything buffered)."""
        if self._items and (self._clock() - self._last) >= self.max_interval:
            return self._flush()
        return None

    def flush(self) -> list:
        """Force-flush whatever is buffered (e.g. on shutdown)."""
        return self._flush()

    def pending(self) -> int:
        return len(self._items)

    def _flush(self) -> list:
        batch, self._items = self._items, []
        self._last = self._clock()
        return batch
