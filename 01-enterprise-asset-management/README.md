# Enterprise Asset Management System (EAMS)

A full-stack system for tracking an organization's physical and digital assets
across their lifecycle: procurement → assignment → maintenance → retirement.

## Problem

Mid-to-large organizations lose real money to poor asset visibility: unknown
software-license exposure, "ghost" hardware that is paid for but unused, missed
maintenance windows, and audit failures because nobody can produce a reliable
chain of custody. Spreadsheets don't scale and don't enforce permissions.

## Solution

A modular, role-based web application:

- **Asset registry** with a typed schema (hardware, software, licenses) and a
  full audit trail of every state change.
- **Lifecycle workflows** (assign, transfer, schedule maintenance, decommission).
- **RBAC** so auditors get read-only views while admins can mutate records.
- **REST API** consumed by a React SPA, designed so a mobile client or
  integration could reuse the same endpoints.

## Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Backend | TypeScript + Fastify | Type safety end-to-end; Fastify's schema validation gives input validation for free |
| Database | PostgreSQL + Prisma | Relational integrity for asset relationships; migrations as code |
| Frontend | React + Vite | Fast, component-driven UI |
| Auth | JWT (access) + httpOnly refresh cookie | Stateless API, XSS-resistant refresh |
| Infra | Docker Compose | One-command local environment |

## Usage

```bash
cp backend/.env.example backend/.env   # then fill in real values
docker compose up --build
# API → http://localhost:4000   Frontend → http://localhost:5173
```

## Security Considerations

- **Secrets** are read exclusively from environment variables; nothing is
  hardcoded. `JWT_SECRET` and `DATABASE_URL` must be provided at runtime.
- **Input validation** is enforced at the API boundary via Fastify JSON
  schemas — requests that don't match the schema are rejected before handlers run.
- **AuthZ** uses role checks on every mutating route (fail-closed default deny).
- **Audit trail** is append-only; records are never hard-deleted, only marked
  retired, preserving chain of custody for compliance.
- **Transport** assumes TLS termination at the proxy; cookies are
  `Secure`+`httpOnly`+`SameSite=Strict`.

## Lessons Learned

- Putting the audit log at the database layer (triggers/append-only table)
  rather than in application code prevents "forgot to log it" gaps.
- Schema-first validation (Fastify + Prisma) removed an entire class of
  defensive `if (!field)` checks from handler code.
- Modeling "retire" as a state transition rather than a delete made compliance
  reporting trivial later.
