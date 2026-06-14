"""Network monitoring collector.

Purpose: Periodically probe TCP reachability + connect latency for configured
targets and export results as Prometheus metrics on /metrics. Classification and
alerting are delegated to the pure `core` module (unit-tested offline).

Security trade-offs:
 - Monitors only the operator-defined targets in targets.yaml (authorized
   assets); uses a plain TCP connect (reachability), not port scanning.
 - Probe concurrency and per-probe timeout are bounded by env config so the
   collector can't be turned into a traffic amplifier.
 - No credentials needed or stored; config comes from the environment.
 - `prometheus_client` and `yaml` are imported lazily so the decision logic in
   `core.py` is testable without them.
"""
from __future__ import annotations

import os
import socket
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .core import AlertConfig, RollingLatency, classify, evaluate_alerts


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


def probe_once(host: str, port: int, timeout: float):
    """TCP-connect probe. Returns (connected, latency_s|None). Never raises."""
    start = time.monotonic()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, time.monotonic() - start
    except OSError:
        return False, None


def load_targets() -> list[dict]:
    import yaml  # lazy
    path = Path(__file__).with_name("targets.yaml")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data.get("targets", [])


def main() -> None:  # pragma: no cover - long-running loop
    from prometheus_client import Gauge, start_http_server  # lazy

    up = Gauge("target_up", "1 if the target TCP port is reachable", ["name", "host"])
    latency = Gauge("target_connect_latency_seconds",
                    "TCP connect latency in seconds", ["name", "host"])

    interval = _env_int("PROBE_INTERVAL_SECONDS", 15)
    timeout = float(os.environ.get("PROBE_TIMEOUT_SECONDS", "2"))
    concurrency = _env_int("PROBE_CONCURRENCY", 8)
    port = _env_int("METRICS_PORT", 9100)
    cfg = AlertConfig(latency_warn_s=float(os.environ.get("LATENCY_WARN_SECONDS", "0.5")))

    targets = load_targets()
    rolling = {t["name"]: RollingLatency() for t in targets}
    start_http_server(port)
    print(f"collector exporting metrics on :{port}, {len(targets)} target(s)")

    def run_probe(t: dict) -> None:
        connected, lat = probe_once(t["host"], int(t["port"]), timeout)
        result = classify(t["name"], t["host"], connected, lat)
        up.labels(result.name, result.host).set(1 if result.up else 0)
        latency.labels(result.name, result.host).set(
            result.latency_s if result.latency_s is not None else float("nan"))
        rolling[result.name].add(result.latency_s)
        for alert in evaluate_alerts(result, cfg):
            print(f"ALERT {alert}")

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        while True:
            for t in targets:
                pool.submit(run_probe, t)
            time.sleep(interval)


if __name__ == "__main__":
    main()
