"""Event enrichment.

Purpose: Add context to a normalized Event before it reaches correlation —
flag internal vs external source IPs and tag known-sensitive accounts. This is
also the correct place to do PII redaction so sensitive values never propagate.

Security trade-offs:
 - IP classification uses the stdlib `ipaddress` module (no external GeoIP
   dependency, no data leaving the host). Private/loopback => internal.
 - Redaction is allow-list based on attribute keys; we strip values for keys
   that look secret rather than trying to detect secrets in free text.
"""
from __future__ import annotations

import ipaddress

from shared.models import Event

# Accounts whose activity is inherently higher-risk; tagged for triage weighting.
_SENSITIVE_USERS = {"root", "administrator", "admin", "svc_backup"}

# Attribute keys whose VALUES we never want to keep verbatim.
_REDACT_KEYS = {"password", "token", "secret", "authorization", "api_key"}


def _is_internal(ip: str | None) -> bool | None:
    if not ip:
        return None
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return None
    return addr.is_private or addr.is_loopback or addr.is_link_local


def enrich(event: Event) -> Event:
    """Mutate-and-return the event with enrichment attributes. Pure/local."""
    internal = _is_internal(event.src_ip)
    if internal is not None:
        event.attributes["src_scope"] = "internal" if internal else "external"

    if event.user and event.user.lower() in _SENSITIVE_USERS:
        event.attributes["sensitive_account"] = "true"

    # Defensive: redact secret-bearing attribute values in place.
    for key in list(event.attributes):
        if key.lower() in _REDACT_KEYS:
            event.attributes[key] = "[REDACTED]"

    return event
