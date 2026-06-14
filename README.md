<!--
  Unified Portfolio Suite - root README
  Purpose: Single entry point describing the monorepo, its 9 flagship projects,
  shared engineering standards, and how to navigate/run each project.
-->

# Unified Portfolio Suite

A monorepo of nine flagship engineering projects spanning full-stack
development, cybersecurity, cloud/DevOps, AI/ML, data engineering, systems
programming, and networking. Each project is self-contained, independently
runnable, and built to the same engineering standards.

> **Status:** Scaffolding complete for all 9 projects. The flagship —
> **Project 09: AI-Powered SOC Platform** — is built out furthest (working
> log-ingestion service, correlation/triage logic, and dashboard structure).

## Projects

| # | Project | Domain | Primary Stack | Manifest |
|---|---------|--------|---------------|----------|
| 01 | [Enterprise Asset Management System](01-enterprise-asset-management/) | Full-Stack | TypeScript · Fastify · React · PostgreSQL | `docker-compose.yml` |
| 02 | [Security Audit Toolkit](02-security-audit-toolkit/) | Cybersecurity | Python · Click | `requirements.txt` |
| 03 | [Multi-Cloud Deployment Platform](03-multi-cloud-deployment-platform/) | Cloud / DevOps | Terraform · Python | `requirements.txt` |
| 04 | [Local AI Security Assistant](04-local-ai-security-assistant/) | AI / ML | Python · Ollama · FAISS | `requirements.txt` |
| 05 | [Real-Time Log Analytics Platform](05-realtime-log-analytics/) | Data Engineering | Kafka · Python · ClickHouse | `docker-compose.yml` |
| 06 | [Mini Operating System Components](06-mini-os-components/) | Systems | C · Make | `Makefile` |
| 07 | [Network Monitoring Suite](07-network-monitoring-suite/) | Networking | Python · Prometheus · Grafana | `docker-compose.yml` |
| 08 | [Security Research & CTF Repository](08-security-research-ctf/) | Open Source | Python · Markdown | `requirements.txt` |
| 09 | [AI-Powered SOC Platform](09-ai-powered-soc-platform/) ⭐ | Flagship | FastAPI · Kafka · React · ML | `docker-compose.yml` |

## Repository layout

```
Unified-Portfolio-Suite/
├── 01-enterprise-asset-management/
├── 02-security-audit-toolkit/
├── 03-multi-cloud-deployment-platform/
├── 04-local-ai-security-assistant/
├── 05-realtime-log-analytics/
├── 06-mini-os-components/
├── 07-network-monitoring-suite/
├── 08-security-research-ctf/
├── 09-ai-powered-soc-platform/   ⭐ flagship
├── docs/                         shared architecture notes
├── .github/workflows/            CI
├── .gitignore                    secret-safe, multi-language
├── LICENSE                       MIT + ethical-use notice
└── README.md                     you are here
```

## Engineering standards (applied to every project)

- **Modularity** — clear separation of concerns; each service/module does one
  thing and exposes a narrow interface.
- **Defensive coding** — validate all external input at boundaries, fail
  closed, no silent `except`/`catch` that swallow errors.
- **No hardcoded secrets** — every credential is read from an environment
  variable. Each project ships a `.env.example` documenting required variables;
  real `.env` files are git-ignored repo-wide.
- **Security by default** — authn/authz, rate limiting, least privilege, and
  input sanitization are designed in, not bolted on. Each README has a
  **Security Considerations** section.
- **Documentation** — every source file opens with a header comment stating its
  purpose and any notable security/performance trade-offs.

## Getting started

Each project is independent. `cd` into a project directory and follow its
README. Most projects run with one of:

```bash
# Containerized projects (01, 05, 07, 09)
docker compose up --build

# Python projects (02, 03, 04, 08)
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Systems project (06)
make && make test
```

## Security & ethical-use notice

This suite contains defensive security tooling intended only for systems you
own or are authorized to assess. See [LICENSE](LICENSE) for the full notice.

## License

[MIT](LICENSE) © 2026 Abdul
