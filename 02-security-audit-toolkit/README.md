# Security Audit Toolkit

A modular, **defensive** command-line toolkit that audits the security posture
of systems and applications **you own or are authorized to assess**.

> ⚠️ **Authorized use only.** Every check in this toolkit is read-only and
> non-intrusive by design. Do not point it at infrastructure you do not own or
> have written permission to test.

## Problem

Security misconfigurations are the most common and most preventable cause of
breaches: missing HTTP security headers, weak TLS settings, dependencies with
known CVEs, world-readable secret files, permissive cloud storage. Teams need a
fast, repeatable way to *self-assess* before an attacker (or auditor) does.

## Solution

A plugin-style toolkit where each "check" is an independent module implementing
a common interface (`run(target) -> Finding[]`). The CLI discovers checks,
runs the selected ones against a target, and produces a severity-ranked report
(human-readable or JSON for CI gating). New checks are added without touching
the core.

## Tech Stack

- **Python 3.12** — ubiquitous, great for tooling and parsing.
- **Click** — ergonomic, well-tested CLI framework.
- **httpx** — modern HTTP client for header/TLS checks.
- **rich** — readable terminal reports.
- Standard library for filesystem-permission and config checks.

## Usage

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# List available checks
python -m audit_toolkit list

# Run HTTP security-header check against a site you own
python -m audit_toolkit run --target https://example.com --check http-headers

# Run all checks and emit JSON (e.g. to fail a CI pipeline on HIGH findings)
python -m audit_toolkit run --target https://example.com --format json
```

## Security Considerations

- **Read-only by contract.** Checks must never modify the target. Anything
  intrusive (active exploitation, fuzzing) is explicitly out of scope.
- **Authorization gate.** The CLI prints an authorization reminder and requires
  `--i-am-authorized` for any network target, making intent explicit.
- **No credentials in code.** Any API tokens a check needs (e.g. for a cloud
  provider) are read from environment variables, never arguments or literals.
- **Safe output.** Findings redact secret values (only their presence/location
  is reported), so reports are safe to attach to tickets.

## Lessons Learned

- A narrow `Check` interface made the toolkit trivially extensible — adding a
  check never required editing the runner.
- Treating findings as structured data (not printed strings) was what enabled
  both pretty reports *and* machine-readable CI gating from the same run.
- An explicit authorization flag is cheap to add and removes ambiguity about
  intended use.
