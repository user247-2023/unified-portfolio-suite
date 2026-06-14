"""Reporting + exit-code logic.

Purpose: Turn a list of `Finding`s into either a human-readable text report or
machine-readable JSON, and decide the process exit code for CI gating. Pure
stdlib so it is unit-testable and has no rendering dependency.

Security note: findings already exclude secret values (see core.Finding), so
both report formats are safe to attach to tickets / CI logs.
"""
from __future__ import annotations

import json
from dataclasses import asdict

from .core import Finding, Severity


def worst_severity(findings: list[Finding]) -> Severity:
    """Highest severity among findings (INFO if empty)."""
    return max((f.severity for f in findings), default=Severity.INFO)


def to_json(findings: list[Finding]) -> str:
    payload = []
    for f in findings:
        d = asdict(f)
        d["severity"] = f.severity.name
        payload.append(d)
    return json.dumps(payload, indent=2)


def to_text(findings: list[Finding]) -> str:
    if not findings:
        return "No findings."
    lines = []
    for f in sorted(findings, key=lambda x: x.severity, reverse=True):
        lines.append(f"[{f.severity.name:8}] {f.check}: {f.title}")
        lines.append(f"           {f.detail}")
        lines.append(f"           fix: {f.remediation}")
    return "\n".join(lines)


def exit_code(findings: list[Finding], fail_on: Severity) -> int:
    """Return 2 if any finding is at/above `fail_on`, else 0 (for CI gating)."""
    return 2 if any(f.severity >= fail_on for f in findings) else 0
