"""Network monitoring collector.

Purpose: Periodically probe TCP reachability + connect latency for configured
targets and export results as Prometheus metrics on /metrics.

Security trade-offs:
 - Monitors only the operator-defined targets in targets.yaml (authorized
   assets), and uses a plain TCP connect (reachability), not port scanning.
 - Probe concurrency and per-probe timeout are bounded by env config so the
   collector can't be turned into a traffic amplifier.
 - No credentials are needed or stored; config comes from the environment.

Performance: probes run in a bounded thread pool so one slow/blackholed target
can't stall the whole cycle.
"""
from __future__ import annotations

import os
import socket
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml
from prometheus_client import Gauge, start_http_server

# Metric: 1 = reachable, 0 = unreachable. Labeled by target name.
UP = Gauge("target_up", "1 if the target TCP port is reachable", ["name", "host"])
LATENCY = Gauge("target_connect_latency_seconds",
                "TCP connect latency in seconds", ["name", "host"])


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


def probe(target: dict, timeout: float) -> None:
    """TCP-connect probe; record up/down + latency. Never raises out."""
    host, port, name = target["host"], int(target["port"]), target["name"]
    start = time.monotonic()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            elapsed = time.monotonic() - start
            UP.labels(name, host).set(1)
            LATENCY.labels(name, host).set(elapsed)
    except OSError:
        # Defensive: a failed probe is data, not an error to crash on.
        UP.labels(name, host).set(0)
        LATENCY.labels(name, host).set(float("nan"))


def load_targets() -> list[dict]:
    path = Path(__file__).with_name("targets.yaml")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data.get("targets", [])


def main() -> None:  # pragma: no cover - long-running loop
    interval = _env_int("PROBE_INTERVAL_SECONDS", 15)
    timeout = float(os.environ.get("PROBE_TIMEOUT_SECONDS", "2"))
    concurrency = _env_int("PROBE_CONCURRENCY", 8)
    port = _env_int("METRICS_PORT", 9100)

    targets = load_targets()
    start_http_server(port)  # exposes /metrics
    print(f"collector exporting metrics on :{port}, {len(targets)} target(s)")

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        while True:
            for t in targets:
                pool.submit(probe, t, timeout)
            time.sleep(interval)


if __name__ == "__main__":
    main()
