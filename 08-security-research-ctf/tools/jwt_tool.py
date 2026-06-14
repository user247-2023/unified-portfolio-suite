"""JWT inspector (defensive).

Purpose: Decode a JSON Web Token's header and payload WITHOUT verifying the
signature, and flag well-known security smells: `alg: none`, weak/symmetric
algorithms where asymmetric is expected, missing expiry, and already-expired
tokens. This is an analysis/triage aid — it never forges or signs tokens.

Usage:
    python tools/jwt_tool.py eyJhbGciOi...
"""
from __future__ import annotations

import argparse
import base64
import json
import time


def _b64url_decode(segment: str) -> bytes:
    """Decode a base64url JWT segment, restoring stripped padding."""
    padding = "=" * (-len(segment) % 4)
    return base64.urlsafe_b64decode(segment + padding)


def decode(token: str) -> tuple[dict, dict]:
    """Return (header, payload) dicts. Raises ValueError on malformed input."""
    parts = token.strip().split(".")
    if len(parts) not in (2, 3):
        raise ValueError("not a JWT (expected 2-3 dot-separated segments)")
    try:
        header = json.loads(_b64url_decode(parts[0]))
        payload = json.loads(_b64url_decode(parts[1]))
    except (ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"could not decode JWT: {exc}") from exc
    return header, payload


def analyze(header: dict, payload: dict, now: int | None = None) -> list[str]:
    """Return a list of security warnings about the token."""
    now = int(time.time()) if now is None else now
    warnings: list[str] = []

    alg = str(header.get("alg", "")).lower()
    if alg in ("none", ""):
        warnings.append("alg=none: signature not enforced — critical if the "
                        "server accepts it (CVE-2015-9235 class).")
    if alg.startswith("hs"):
        warnings.append("HMAC alg (HS*): vulnerable to key-confusion if the "
                        "server also accepts RS* with the public key as secret.")

    if "exp" not in payload:
        warnings.append("no 'exp' claim: token never expires.")
    elif isinstance(payload["exp"], (int, float)) and payload["exp"] < now:
        warnings.append(f"expired: exp={payload['exp']} < now={now}.")

    if "alg" in header and "kid" in header:
        warnings.append("'kid' present: review for path-traversal / SQL-injection "
                        "in key lookup.")
    return warnings or ["no obvious issues detected (signature NOT verified)."]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Decode + analyze a JWT (no verify).")
    parser.add_argument("token")
    args = parser.parse_args(argv)
    try:
        header, payload = decode(args.token)
    except ValueError as exc:
        print(f"error: {exc}")
        return 1
    print("header:", json.dumps(header))
    print("payload:", json.dumps(payload))
    print("warnings:")
    for w in analyze(header, payload):
        print(f"  - {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
