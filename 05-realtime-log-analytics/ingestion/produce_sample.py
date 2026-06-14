"""Sample producer for local testing.

Purpose: Emit a few well-formed (and one malformed) log events to the raw topic
so you can watch the processor batch good events and dead-letter bad ones.
Security note: broker address comes from KAFKA_BOOTSTRAP env, not a literal.
"""
from __future__ import annotations

import json
import os
import time


def main() -> None:  # pragma: no cover - requires live Kafka
    from confluent_kafka import Producer

    producer = Producer({"bootstrap.servers": os.environ.get("KAFKA_BOOTSTRAP", "localhost:9092")})
    topic = os.environ.get("KAFKA_TOPIC", "logs.raw")

    samples = [
        {"ts": time.time(), "service": "api", "level": "INFO", "message": "request ok"},
        {"ts": time.time(), "service": "api", "level": "ERROR", "message": "db timeout",
         "trace_id": "abc123", "attributes": {"status": "500"}},
        {"service": "api", "message": "missing ts -> dead-letter"},  # malformed
    ]
    for s in samples:
        producer.produce(topic, json.dumps(s).encode("utf-8"))
    producer.flush()
    print(f"produced {len(samples)} events to {topic}")


if __name__ == "__main__":
    main()
