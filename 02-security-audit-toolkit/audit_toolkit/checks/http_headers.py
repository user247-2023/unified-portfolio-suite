"""HTTP security-header check.

Purpose: Read-only check that fetches a URL and reports missing or weak HTTP
security headers (HSTS, CSP, X-Content-Type-Options, etc.).

Design: the scoring logic lives in a PURE function `evaluate_headers(present)`
so it can be unit-tested offline; `run()` only does the (network) I/O and then
delegates. `httpx` is imported lazily inside `run()` so the toolkit — and its
test suite — import cleanly without the dependency installed.

Security trade-off: issues a single GET with a short timeout and capped
redirects (non-intrusive). Reports only header presence (no body, no secrets).
"""
from __future__ import annotations

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


def evaluate_headers(present_headers: dict | None,
                     status_code: int = 0) -> list[Finding]:
    """Pure evaluation: given the response headers (case-insensitive keys),
    return findings. No I/O — unit-testable offline."""
    present = {k.lower() for k in (present_headers or {})}
    findings: list[Finding] = []
    for header, severity, remediation in _EXPECTED_HEADERS:
        if header not in present:
            findings.append(Finding(
                check="http-headers", severity=severity,
                title=f"Missing header: {header}",
                detail=f"Response did not return `{header}`.",
                remediation=remediation,
                evidence=f"HTTP {status_code}" if status_code else "",
            ))
    if not findings:
        findings.append(Finding(
            check="http-headers", severity=Severity.INFO,
            title="All baseline security headers present",
            detail="The response returned the expected security headers.",
            remediation="No action required.",
        ))
    return findings


@register
class HttpHeadersCheck:
    name = "http-headers"
    description = "Audit HTTP security response headers for a URL."

    def run(self, target: str) -> list[Finding]:
        import httpx  # lazy: keeps the package importable without the dep

        try:
            resp = httpx.get(target, timeout=10.0, follow_redirects=True,
                             headers={"User-Agent": "security-audit-toolkit/0.1"})
        except httpx.HTTPError as exc:
            return [Finding(
                check=self.name, severity=Severity.INFO,
                title="Target unreachable",
                detail=f"Could not fetch {target}: {exc.__class__.__name__}",
                remediation="Verify the URL and your authorization to test it.",
            )]
        return evaluate_headers(dict(resp.headers), resp.status_code)
