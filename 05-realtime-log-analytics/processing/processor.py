"""Kafka -> ClickHouse stream processor.

Purpose: Consume raw log events from Kafka, validate/parse them (via the pure
`core` module), batch them, and insert into ClickHouse. Malformed events are
routed to a dead-letter topic.

Security / correctness trade-offs:
 - Offsets are committed only AFTER a successful insert => at-least-once delivery
   (we prefer duplicates over data loss).
 - Validation/batching live in `core.py` (pure stdlib, unit-tested); this module
   only wires them to the real clients, which are imported lazily so the package
   stays importable without the infra installed.
 - All connection settings come from the environment (no literals).
"""
from __future__ import annotations

import os

from .core import Batcher, Event, parse_event  # noqa: F401  (re-exported)


def env(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if value is None:
        raise RuntimeError(f"missing required environment variable: {name}")
    return value


def run() -> None:  # pragma: no cover - requires live Kafka/ClickHouse
    """Main consume->batch->insert loop."""
    from confluent_kafka import Consumer, Producer
    import clickhouse_connect

    consumer = Consumer({
        "bootstrap.servers": env("KAFKA_BOOTSTRAP"),
        "group.id": env("KAFKA_GROUP_ID", "log-processor"),
        "enable.auto.commit": False,  # commit only after a successful insert
        "auto.offset.reset": "earliest",
    })
    dlq = Producer({"bootstrap.servers": env("KAFKA_BOOTSTRAP")})
    ch = clickhouse_connect.get_client(
        host=env("CLICKHOUSE_HOST"), port=int(env("CLICKHOUSE_PORT", "8123")),
        username=env("CLICKHOUSE_USER"), password=env("CLICKHOUSE_PASSWORD"),
        database=env("CLICKHOUSE_DB", "logs"),
    )

    consumer.subscribe([env("KAFKA_TOPIC", "logs.raw")])
    batcher = Batcher(
        max_size=int(env("BATCH_SIZE", "1000")),
        max_interval=float(env("FLUSH_INTERVAL_SECONDS", "2")),
    )

    try:
        while True:
            msg = consumer.poll(0.5)
            batch = None
            if msg is not None and not msg.error():
                try:
                    batch = batcher.add(parse_event(msg.value()))
                except ValueError:
                    dlq.produce(env("KAFKA_DLQ_TOPIC", "logs.deadletter"),
                                msg.value())
            batch = batch or batcher.tick()
            if batch:
                _insert(ch, batch)
                consumer.commit(asynchronous=False)  # durability checkpoint
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
