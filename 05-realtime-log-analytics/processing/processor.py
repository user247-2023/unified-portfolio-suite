"""Kafka -> ClickHouse stream processor.

Purpose: Consume raw log events from Kafka, validate/parse them, batch them, and
insert into ClickHouse. Malformed events are routed to a dead-letter topic.

Security / correctness trade-offs:
 - Offsets are committed only AFTER a successful insert => at-least-once delivery
   (we prefer duplicates over data loss).
 - Every event is validated before insert; bad events are dead-lettered, never
   silently dropped and never allowed to crash the consumer loop.
 - All connection settings come from the environment (no literals).

Performance: events are flushed in batches of BATCH_SIZE or every
FLUSH_INTERVAL_SECONDS, whichever comes first — amortizing insert cost.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass


@dataclass
class Event:
    ts: float
    service: str
    level: str
    message: str
    trace_id: str
    attributes: dict


def parse_event(raw: bytes) -> Event:
    """Validate and coerce a raw Kafka payload into an Event.

    Raises ValueError on anything malformed so the caller can dead-letter it.
    """
    data = json.loads(raw)  # raises on invalid JSON -> dead-letter
    try:
        return Event(
            ts=float(data["ts"]),
            service=str(data["service"])[:128],
            level=str(data.get("level", "INFO"))[:16],
            message=str(data["message"])[:8192],
            trace_id=str(data.get("trace_id", "")),
            attributes={str(k): str(v) for k, v in data.get("attributes", {}).items()},
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid event schema: {exc}") from exc


def env(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if value is None:
        raise RuntimeError(f"missing required environment variable: {name}")
    return value


def run() -> None:  # pragma: no cover - requires live Kafka/ClickHouse
    """Main consume->batch->insert loop. Imports clients lazily so this module
    is importable (and unit-testable) without the infra installed."""
    from confluent_kafka import Consumer, Producer
    import clickhouse_connect

    consumer = Consumer({
        "bootstrap.servers": env("KAFKA_BOOTSTRAP"),
        "group.id": env("KAFKA_GROUP_ID", "log-processor"),
        "enable.auto.commit": False,  # we commit only after a successful insert
        "auto.offset.reset": "earliest",
    })
    dlq = Producer({"bootstrap.servers": env("KAFKA_BOOTSTRAP")})
    ch = clickhouse_connect.get_client(
        host=env("CLICKHOUSE_HOST"), port=int(env("CLICKHOUSE_PORT", "8123")),
        username=env("CLICKHOUSE_USER"), password=env("CLICKHOUSE_PASSWORD"),
        database=env("CLICKHOUSE_DB", "logs"),
    )

    consumer.subscribe([env("KAFKA_TOPIC", "logs.raw")])
    batch_size = int(env("BATCH_SIZE", "1000"))
    flush_interval = float(env("FLUSH_INTERVAL_SECONDS", "2"))

    batch: list[Event] = []
    last_flush = time.monotonic()
    try:
        while True:
            msg = consumer.poll(0.5)
            if msg is not None and not msg.error():
                try:
                    batch.append(parse_event(msg.value()))
                except ValueError:
                    dlq.produce(env("KAFKA_DLQ_TOPIC", "logs.deadletter"),
                                msg.value())

            due = (len(batch) >= batch_size or
                   time.monotonic() - last_flush >= flush_interval)
            if batch and due:
                _insert(ch, batch)
                consumer.commit(asynchronous=False)  # durability checkpoint
                batch.clear()
                last_flush = time.monotonic()
    finally:
        consumer.close()


def _insert(ch, batch: list[Event]) -> None:  # pragma: no cover
    ch.insert(
        "events",
        [[e.ts, e.service, e.level, e.message, e.trace_id, e.attributes]
         for e in batch],
        column_names=["ts", "service", "level", "message", "trace_id", "attributes"],
    )


if __name__ == "__main__":
    run()
