# AI-Powered SOC Platform — Architecture

## Component / data flow

```
                         ┌──────────────────────────────────────────┐
   producers             │            INGESTION SERVICE             │
 (sshd, firewall,  HTTP  │             (FastAPI, :8000)             │
  apps, agents) ───────▶ │  auth (X-API-Key, fail-closed)           │
                         │  validate (Pydantic) ─▶ Pipeline.process │
                         └───────────────┬──────────────────────────┘
                                         │ canonical Event
                  ┌──────────────────────▼──────────────────────┐
                  │                  PIPELINE                    │
                  │  normalize ─▶ enrich ─▶ correlate ─▶ triage  │
                  └───────┬───────────┬──────────┬──────────┬────┘
                          │           │          │          │
                    Event(canonical)  │     Alert(s)    Incident(s)
                          │      (src_scope,        (risk_score,
                          │       sensitive,         priority,
                          │       redaction)         rationale,
                          │                          playbook)
                                                          │
                         ┌────────────────────────────────▼─────────┐
                         │            SIEM DASHBOARD                 │
                         │        (React/Vite, :8080)                │
                         │  polls /incidents, renders the queue      │
                         └───────────────────────────────────────────┘
```

## Modules

| Module | Path | Responsibility | Deps |
|--------|------|----------------|------|
| Domain models | `shared/models.py` | `Event`, `Alert`, `Incident`, `Severity`, `Priority` | stdlib |
| Config | `shared/config.py` | env-driven settings, fail-closed key | stdlib |
| Normalizer | `services/ingestion/app/normalizer.py` | raw → canonical `Event` | stdlib |
| Enrichment | `services/ingestion/app/enrichment.py` | IP scope, sensitive accounts, redaction | stdlib |
| Rules | `services/correlation/app/rules.py` | pure detection functions | stdlib |
| Correlation engine | `services/correlation/app/engine.py` | windowed per-entity state, dedupe | stdlib |
| Scoring | `services/triage/app/scoring.py` | explainable 0–100 risk score | stdlib |
| Playbooks | `services/triage/app/playbooks.py` | defensive response actions | stdlib |
| Triage | `services/triage/app/triage.py` | group → score → prioritize | stdlib |
| Ingestion API | `services/ingestion/app/main.py` | HTTP edge | FastAPI |
| Dashboard | `dashboard/` | SIEM UI | React/Vite |

The detection core depends only on the standard library; FastAPI/React live at
the edges. This keeps the security-critical logic testable in CI with no
infrastructure.

## Design decisions & trade-offs

1. **Single canonical schema.** All sources normalize to one `Event`. Cost: a
   normalizer per source. Benefit: correlation/triage are tiny and source-agnostic.
2. **Explainable scoring over ML.** A transparent weighted heuristic with a
   per-point rationale. Trade-off: less "automatic" than a learned model, but
   tunable and trustworthy — the right call for a SOC. Clean seam to add ML later.
3. **In-memory correlation state.** Simple and fast for a single node and for
   deterministic tests. **Production swap point:** back the window with a
   durable, shardable store (Redis Streams / Kafka + state store) so state
   survives restarts and scales horizontally.
4. **Recommend, never auto-remediate.** Heuristic-driven auto-blocking risks
   self-inflicted DoS (spoofed source IPs). Auto-response must be gated behind
   explicit approval and allow-lists.

## Production hardening roadmap

- Durable event bus (Kafka) between ingestion and correlation; horizontal
  consumers with partitioned-by-entity state.
- Persistent incident store (Postgres) + full-text search over events.
- User authentication (SSO/OIDC) on the dashboard; API-key auth is for
  machine producers only.
- More detections (impossible travel, data-exfil volume, MITRE ATT&CK mapping).
- Optional ML risk model behind the existing scoring interface, with the
  heuristic kept as an explainable fallback.
- Offline LLM incident summaries via the
  [Local AI Security Assistant](../../04-local-ai-security-assistant/).
