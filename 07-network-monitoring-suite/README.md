# Network Monitoring Suite

A passive network monitoring stack that collects availability and latency
metrics for hosts/services **you operate**, exposes them in Prometheus format,
and visualizes them in Grafana with alerting.

## Problem

You can't fix what you can't see. Without continuous monitoring, the first sign
of a network problem is a user complaint. Teams need real-time visibility into
reachability, latency, and packet loss across their own infrastructure, plus
alerts before users notice.

## Solution

- **Collector** — a Python agent that periodically probes configured targets
  (ICMP/TCP reachability + latency) and exposes the results as Prometheus
  metrics over an HTTP `/metrics` endpoint.
- **Prometheus** scrapes the collector and stores time-series data.
- **Grafana** dashboards visualize latency/uptime; Prometheus alert rules fire
  on loss or latency SLO breaches.

This is **passive, defensive monitoring** of your own assets — not scanning or
probing third-party networks.

## Tech Stack

- **Python + prometheus_client** — metrics collector/exporter.
- **Prometheus** — scraping + alerting.
- **Grafana** — dashboards.
- **Docker Compose** — one-command stack.

## Usage

```bash
cp .env.example .env
# edit collector/targets.yaml with hosts YOU operate
docker compose up --build
# Grafana → http://localhost:3000   Prometheus → http://localhost:9090

# Run the offline core tests (probe classification + alert rules; pure stdlib):
python -m unittest discover -s tests -v
```

Probe classification, rolling-latency tracking, and alert evaluation live in
`collector/core.py` (pure stdlib, unit-tested). `collector.py` does the socket
I/O and metric export, importing `prometheus_client`/`yaml` lazily so the
decision logic is testable without them.

## Security Considerations

- **Authorized targets only.** The collector monitors hosts listed in your own
  `targets.yaml`; this suite is for infrastructure you operate. It performs
  reachability/latency probes, not port scanning or service enumeration.
- **No hardcoded secrets.** Grafana admin credentials and any auth come from
  environment variables (`.env.example`).
- **Least exposure.** The collector binds its metrics endpoint to the internal
  Docker network; only Grafana is meant to be user-facing (behind auth).
- **Resource bounds.** Probe concurrency and timeouts are capped so the
  collector can't be turned into a traffic amplifier.

## Lessons Learned

- Exposing metrics in Prometheus format (rather than a bespoke API) meant
  Grafana, alerting, and long-term storage all worked for free.
- Capping probe concurrency/timeout up front kept a misconfigured target list
  from turning the monitor into a noisy neighbor.
- Separating "collect" (the agent) from "store/visualize" (Prometheus/Grafana)
  made each piece independently replaceable.
