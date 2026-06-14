"""TLS certificate expiry check.

Purpose: Connect to a host's TLS port, read the leaf certificate's validity
window, and warn when it is expired or expiring soon. Expired/near-expiry certs
cause outages and erode trust.

Design: the date logic is a PURE function `evaluate_validity(not_after, now)`
(unit-testable offline); `run()` only does the TLS handshake (stdlib `ssl`, no
third-party dependency) and parses the cert's `notAfter`.

Security trade-off: a single short-timeout handshake; we read metadata only and
never send application data. Certificate verification is left ON.
"""
from __future__ import annotations

import socket
import ssl
from datetime import datetime, timezone

from ..core import Finding, Severity, register

_WARN_DAYS = 30   # warn when fewer than this many days remain


def evaluate_validity(not_after_epoch: float, now_epoch: float,
                      host: str = "") -> list[Finding]:
    """Pure: classify a cert's remaining lifetime into a finding."""
    days_left = (not_after_epoch - now_epoch) / 86400.0
    where = f" for {host}" if host else ""
    if days_left < 0:
        return [Finding(
            check="tls-cert", severity=Severity.CRITICAL,
            title=f"TLS certificate expired{where}",
            detail=f"Certificate expired {abs(days_left):.1f} days ago.",
            remediation="Renew and deploy a valid certificate immediately.",
        )]
    if days_left < _WARN_DAYS:
        return [Finding(
            check="tls-cert", severity=Severity.HIGH,
            title=f"TLS certificate expiring soon{where}",
            detail=f"Certificate expires in {days_left:.1f} days.",
            remediation="Renew before expiry; automate renewal (e.g. ACME).",
        )]
    return [Finding(
        check="tls-cert", severity=Severity.INFO,
        title=f"TLS certificate valid{where}",
        detail=f"Certificate valid for another {days_left:.1f} days.",
        remediation="No action required.",
    )]


def _parse_not_after(value: str) -> float:
    """Parse OpenSSL's notAfter format, e.g. 'Jun 14 12:00:00 2027 GMT'."""
    dt = datetime.strptime(value, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
    return dt.timestamp()


@register
class TlsCertCheck:
    name = "tls-cert"
    description = "Check a host's TLS certificate expiry (host[:port])."

    def run(self, target: str) -> list[Finding]:
        host, _, port_s = target.replace("https://", "").partition(":")
        port = int(port_s) if port_s.isdigit() else 443
        ctx = ssl.create_default_context()
        try:
            with socket.create_connection((host, port), timeout=10) as sock:
                with ctx.wrap_socket(sock, server_hostname=host) as tls:
                    cert = tls.getpeercert()
        except (OSError, ssl.SSLError) as exc:
            return [Finding(
                check=self.name, severity=Severity.INFO,
                title="TLS handshake failed",
                detail=f"Could not retrieve a certificate from {target}: "
                       f"{exc.__class__.__name__}",
                remediation="Verify the host/port and your authorization to test it.",
            )]
        not_after = _parse_not_after(cert["notAfter"])
        now = datetime.now(timezone.utc).timestamp()
        return evaluate_validity(not_after, now, host)
