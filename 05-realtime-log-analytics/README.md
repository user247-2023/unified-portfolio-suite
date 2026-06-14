# Real-Time Log Analytics Platform

A streaming pipeline that ingests high-volume log events, processes them in near
real time, and stores them in a columnar database for sub-second analytical
queries and alerting.

## Problem

Application and infrastructure logs arrive as a firehose. Batch-loading them into
a relational database is too slow for operational visibility, and grepping flat
files doesn't scale. Teams need to ask "what's happening right now?" and get an
answer in milliseconds, over billions of rows.

## Solution

A classic, robust streaming architecture:

```
producers ──▶ Kafka topic ──▶ stream processor ──▶ ClickHouse ──▶ queries/alerts
              (durable buffer)   (parse, enrich,     (columnar OLAP)
                                  validate, batch)
```

- **Kafka** decouples producers from consumers and absorbs spikes (back-pressure
  via a durable log).
- **Stream processor** (Python consumer) parses, validates, and enriches events,
  then batch-inserts into ClickHouse for efficiency.
- **ClickHouse** answers aggregation queries over huge volumes in real time.

## Tech Stack

- **Apache Kafka** — durable, partitioned event log.
- **Python + confluent-kafka** — consumer/processor.
- **ClickHouse** — columnar OLAP store.
- **Docker Compose** — one-command local stack.

## Usage

```bash
cp .env.example .env
docker compose up --build
# Kafka broker, ClickHouse, and the processor all start.

# Produce a sample event (see processing/ for the schema):
python ingestion/produce_sample.py

# Run the offline core tests (event parsing + batching; pure stdlib):
python -m unittest discover -s tests -v
```

The parse/validate and batching logic lives in `processing/core.py` (pure
stdlib, unit-tested with an injectable clock for deterministic interval
flushing). `processor.py` only wires that core to Kafka/ClickHouse, importing
those clients lazily so the package stays importable without the infrastructure.

## Security Considerations

- **No hardcoded credentials.** Broker addresses and ClickHouse auth come from
  environment variables (`.env.example` documents them).
- **Input validation at the boundary.** The processor validates and coerces
  every event against a schema before insert; malformed events go to a
  dead-letter topic instead of crashing the consumer (fail-safe, not fail-open).
- **Least-privilege DB user.** The processor connects with an INSERT-only
  ClickHouse user; read dashboards use a separate read-only user.
- **PII hygiene.** The enrichment stage is where field-level redaction/hashing
  belongs so sensitive values aren't persisted in plaintext.
- **Back-pressure, not data loss.** Kafka retention + consumer offset commits
  after successful insert give at-least-once delivery semantics.

## Lessons Learned

- Committing Kafka offsets only *after* a successful ClickHouse insert was the
  difference between "we lost an hour of logs" and at-least-once durability.
- Batching inserts (rather than row-at-a-time) was the single biggest throughput
  win with ClickHouse.
- A dead-letter topic for unparseable events kept one bad producer from halting
  the whole pipeline.
