# AI-Powered SOC Platform ⭐ (Flagship)

A modular Security Operations Center platform that ingests security logs in a
canonical schema, correlates them into detections in real time, and **auto-triages**
the results into a prioritized, explainable incident queue with recommended
response playbooks.

> Built furthest of the nine projects. The detection core
> (normalize → enrich → correlate → triage) is **runnable and unit-tested today**
> with zero third-party dependencies (`python seed_demo.py`).

## Problem

SOC analysts drown in alerts. A typical SIEM emits thousands of low-context
events per day; the real signal — "an external host just brute-forced root and
*succeeded*" — is buried. Analysts burn out triaging noise, and the incidents
that matter are found late. Worse, many tools score risk with opaque models
nobody trusts or can tune.

## Solution

A pipeline of small, independently testable stages built on **one canonical
event schema**:

```
 raw logs ─▶ INGESTION ─▶ NORMALIZE ─▶ ENRICH ─▶ CORRELATE ─▶ TRIAGE ─▶ Incident queue
 (any source)  (FastAPI)   (1 schema)  (context)  (rules →     (score →    (SIEM dashboard)
                                                   alerts)      priority +
                                                                playbook)
```

- **Ingestion service** (FastAPI) — authenticated, validated, fail-closed entry
  point for batches of raw events.
- **Normalizer** — maps SSH/firewall/generic logs into one `Event` type so
  everything downstream is source-agnostic.
- **Enrichment** — tags internal vs external IPs (stdlib, no GeoIP call) and
  sensitive accounts; redacts secret-bearing fields.
- **Correlation engine** — windowed, per-entity, rule-based detection
  (brute force, successful-brute-force, port scan) producing de-duplicated alerts.
- **Triage** — *automated incident triage logic*: groups alerts, computes a
  transparent 0–100 risk score **with a line-by-line rationale**, assigns
  P1–P4 priority, and attaches a defensive response playbook.
- **SIEM dashboard** (React/Vite) — prioritized incident queue showing the
  score rationale and recommended actions.

### Why "AI-powered" here means *explainable*

The risk scorer is a transparent weighted heuristic, not a black box. Every
incident carries the exact reasons for its score (see the live output below).
This is a deliberate SOC design choice — an analyst will tune and trust a score
they can read. The architecture leaves a clean seam to swap in an ML model
later, and the [Local AI Security Assistant](../04-local-ai-security-assistant/)
provides offline LLM summarization without sending data off-host.

## Tech Stack

| Concern | Choice | Why |
|---------|--------|-----|
| Ingestion API | FastAPI + Pydantic | Schema validation + speed at the edge |
| Core logic | Pure Python (stdlib) | Zero-dependency, testable anywhere |
| Dashboard | React + Vite | Component-driven SIEM UI |
| Packaging | Docker Compose | One-command stack |

## Usage

```bash
# Fastest: run the detection core end-to-end, no install needed.
python seed_demo.py

# Run the test suite (stdlib unittest — no pip install required):
python -m unittest discover -s tests -v

# Full stack (API + dashboard):
cp .env.example .env          # set a strong INGEST_API_KEY
docker compose up --build
# Ingestion API → http://localhost:8000   Dashboard → http://localhost:8080

# Send events to the API:
curl -X POST http://localhost:8000/ingest \
  -H "X-API-Key: $INGEST_API_KEY" -H "content-type: application/json" \
  -d '{"source":"sshd","events":[{"src_ip":"45.9.148.99","user":"root","outcome":"failure"}]}'
```

### Live output (`python seed_demo.py`)

A burst of failed root logins followed by a success, from an external IP:

```
priority P1  score 95
+50 base from highest severity (CRITICAL).
+5  for 2 correlated alerts.
+15 external source IP involved.
+15 sensitive account targeted.
+10 multiple distinct detections (brute_force, successful_brute_force).
= final risk score 95/100  → P1 (auto-escalate at 80)
```

## Security Considerations

- **Fail-closed auth.** `/ingest` requires `X-API-Key`, compared in constant
  time (`hmac.compare_digest`). If `INGEST_API_KEY` is unset the service returns
  503 rather than accepting unauthenticated data.
- **No hardcoded secrets / thresholds.** Everything tunable comes from env via
  `shared/config.py`; `.env` is git-ignored.
- **Input validation + DoS bounds.** Pydantic validates each request; batch size
  and field lengths are capped; the normalizer truncates oversized fields.
- **Secret redaction at the edge.** Enrichment redacts secret-bearing attribute
  values before they reach storage or the dashboard.
- **Recommend, don't auto-remediate.** Triage attaches response *recommendations*
  for human/SOAR approval. Auto-blocking on a heuristic (e.g. a spoofed source
  IP) risks self-inflicted DoS — see `services/triage/app/playbooks.py`.
- **Containers run non-root.**

## Lessons Learned

- **One canonical schema** was the highest-leverage decision — it kept
  correlation and triage tiny and source-agnostic.
- **Explainable scoring beat a black box.** Shipping the rationale with every
  incident is what made the output trustworthy and tunable.
- **Keeping the core dependency-free** meant the detection logic is testable in
  CI with no infrastructure, while FastAPI/Docker stay at the edges.
- **Committing offsets/state only after success** (a lesson shared with
  [Project 05](../05-realtime-log-analytics/)) matters wherever durability does;
  here the in-memory store is explicitly flagged as the production swap point.

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the component diagram, data
flow, and the scaling/production hardening roadmap.
