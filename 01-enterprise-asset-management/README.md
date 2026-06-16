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

Run the domain test suite — **no install needed** (uses Node's built-in test
runner against the dependency-free lifecycle domain):

```bash
cd backend && node --test        # or: npm test
```

Run the **frontend**. It probes the API on startup: if the backend is up it
talks to it **live** (using a dev session token); otherwise it falls back to an
in-memory **demo** store that mirrors the same rules, so it always runs. The
badge in the header shows which mode you're in.

```bash
# Standalone (demo mode — no backend needed):
cd frontend && npm install && npm run dev          # → http://localhost:5174

# Wired to the live API (start the backend first):
#   1) backend:  JWT_SECRET=dev NODE_ENV=development npm run dev   (port 4000)
#   2) frontend: npm run dev                                       (auto-detects it)
```

The console lets you register assets, drive the lifecycle (assign → maintenance
→ retire), and switch between an **Admin** and **Auditor** role to see RBAC in
action (auditors can read, but mutations are rejected — the API returns 403 and
the demo store throws the same way). The append-only audit trail updates live,
and the UI only ever offers transitions the state machine permits.

### API endpoints (used by the frontend)

| Method & path | Auth | Purpose |
|---|---|---|
| `POST /auth/dev-token` | — (dev only) | Mint a role token for local development |
| `GET /assets` | any user | List assets |
| `GET /audit` | any user | Append-only audit trail (newest first) |
| `POST /assets` | admin | Register an asset |
| `POST /assets/:id/assign` | admin | Assign to a user |
| `POST /assets/:id/maintenance` | admin | Move to maintenance |
| `POST /assets/:id/retire` | admin | Retire (terminal) |

CORS is restricted to `CORS_ORIGINS` (default the local frontend origin).

The business rules (lifecycle state machine, RBAC default-deny, append-only
audit trail) live in `backend/src/domain/assets.mjs` as a pure, framework-free
module. The Fastify routes wrap that domain — keeping the rules testable without
spinning up a server or database.

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
