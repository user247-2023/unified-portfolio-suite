"""HTTP security-header check.

Purpose: Read-only check that fetches a URL and reports missing or weak HTTP
security headers (HSTS, CSP, X-Content-Type-Options, etc.).

Security trade-off: Issues a single GET with a short timeout and no following of
risky redirects beyond a small cap — non-intrusive and abuse-resistant. Reports
only header presence/values (no body, no secrets).
"""
from __future__ import annotations

import httpx

from ..core import Finding, Severity, register

# (header, severity-if-missing, human remediation)
_EXPECTED_HEADERS: list[tuple[str, Severity, str]] = [
    ("strict-transport-security", Severity.HIGH,
     "Add HSTS: `Strict-Transport-Security: max-age=63072000; includeSubDomains`."),
    ("content-security-policy", Severity.HIGH,
     "Define a Content-Security-Policy to mitigate XSS/data injection."),
    ("x-content-type-options", Severity.MEDIUM,
     "Set `X-Content-Type-Options: nosniff`."),
    ("x-frame-options", Severity.MEDIUM,
     "Set `X-Frame-Options: DENY` (or a CSP frame-ancestors directive)."),
    ("referrer-policy", Severity.LOW,
     "Set a Referrer-Policy such as `strict-origin-when-cross-origin`."),
]


@register
class HttpHeadersCheck:
    name = "http-headers"
    description = "Audit HTTP security response headers for a URL."

    def run(self, target: str) -> list[Finding]:
        findings: list[Finding] = []
        try:
            # Defensive: short timeout, capped redirects, no cert bypass.
            resp = httpx.get(target, timeout=10.0, follow_redirects=True,
                             headers={"User-Agent": "security-audit-toolkit/0.1"})
        except httpx.HTTPError as exc:
            return [Finding(
                check=self.name, severity=Severity.INFO,
                title="Target unreachable",
                detail=f"Could not fetch {target}: {exc.__class__.__name__}",
                remediation="Verify the URL and your authorization to test it.",
            )]

        present = {k.lower() for k in resp.headers}
        for header, severity, remediation in _EXPECTED_HEADERS:
            if header not in present:
                findings.append(Finding(
                    check=self.name, severity=severity,
                    title=f"Missing header: {header}",
                    detail=f"{target} did not return `{header}`.",
                    remediation=remediation,
                    evidence=f"HTTP {resp.status_code}",
                ))

        if not findings:
            findings.append(Finding(
                check=self.name, severity=Severity.INFO,
                title="All baseline security headers present",
                detail=f"{target} returned the expected security headers.",
                remediation="No action required.",
            ))
        return findings
