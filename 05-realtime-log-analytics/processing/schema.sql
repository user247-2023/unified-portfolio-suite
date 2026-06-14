-- ----------------------------------------------------------------------------
-- ClickHouse schema for ingested logs.
-- Purpose: A MergeTree table partitioned by day and ordered for the common
-- query pattern (filter by service + time range).
-- Performance note: ORDER BY (service, ts) gives data skipping on the hot path;
-- partitioning by day keeps parts manageable and makes TTL-based retention cheap.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS logs.events
(
    ts          DateTime64(3)         CODEC(DoubleDelta, ZSTD),
    service     LowCardinality(String),
    level       LowCardinality(String),
    message     String                CODEC(ZSTD),
    trace_id    String,
    attributes  Map(String, String)
)
ENGINE = MergeTree
PARTITION BY toDate(ts)
ORDER BY (service, ts)
TTL toDateTime(ts) + INTERVAL 30 DAY;   -- retention; tune per compliance needs
