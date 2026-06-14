"""Response playbooks.

Purpose: Map each detection rule to a list of recommended, DEFENSIVE response
actions. Triage attaches these to an incident so a responder has an immediate,
consistent starting checklist.

Important: these are *recommendations for a human/SOAR to review and approve*,
not auto-executed actions. Automatically blocking/isolating based on a heuristic
risks self-inflicted denial of service (e.g. a spoofed source IP causing you to
block a legitimate one). Auto-remediation, if added, must be gated behind
explicit approval and allow-lists.
"""
from __future__ import annotations

_PLAYBOOKS: dict[str, list[str]] = {
    "brute_force": [
        "Review the source IP's reputation and recent history.",
        "Rate-limit or temporarily block the source IP at the edge (after review).",
        "Confirm the targeted account(s) are not compromised; enforce MFA.",
    ],
    "successful_brute_force": [
        "Treat the affected account as compromised: reset credentials, revoke sessions/tokens.",
        "Isolate the affected host pending investigation.",
        "Hunt for lateral movement and persistence from the entity/host.",
        "Preserve logs for forensics before remediation.",
    ],
    "port_scan": [
        "Verify which scanned services are actually exposed and whether they should be.",
        "Block or rate-limit the scanning source at the firewall (after review).",
        "Confirm exposed services are patched and access-controlled.",
    ],
}

_DEFAULT = [
    "Triage manually: validate the alert, gather context, and document findings.",
]


def actions_for(rule: str) -> list[str]:
    """Recommended response actions for a rule (defensive copy)."""
    return list(_PLAYBOOKS.get(rule, _DEFAULT))


def actions_for_alerts(rules: set[str]) -> list[str]:
    """Merge, de-duplicate (preserving order), and return actions for a set of
    triggered rules."""
    seen: set[str] = set()
    merged: list[str] = []
    for rule in sorted(rules):
        for action in actions_for(rule):
            if action not in seen:
                seen.add(action)
                merged.append(action)
    return merged or list(_DEFAULT)
