"""Hash identifier.

Purpose: Given a hash string, suggest likely algorithms based on length and
character set. A common first step in CTF crypto/forensics challenges. Purely
analytical — it inspects a string, it does not crack anything.

Usage:
    python tools/hashid.py 5f4dcc3b5aa765d61d8327deb882cf99
"""
from __future__ import annotations

import argparse
import re

# (name, hex length, regex) — ordered roughly by how common they are in CTFs.
_HEX_HASHES: list[tuple[str, int]] = [
    ("MD5", 32),
    ("SHA-1", 40),
    ("SHA-224", 56),
    ("SHA-256", 64),
    ("SHA-384", 96),
    ("SHA-512", 128),
]

_HEX_RE = re.compile(r"^[0-9a-fA-F]+$")
_BCRYPT_RE = re.compile(r"^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}$")
_ARGON2_RE = re.compile(r"^\$argon2(id|i|d)\$")
_SHA512_CRYPT_RE = re.compile(r"^\$6\$")
_MD5_CRYPT_RE = re.compile(r"^\$1\$")


def identify(value: str) -> list[str]:
    """Return candidate algorithm names for `value`, most-likely first."""
    value = value.strip()
    if not value:
        return []

    # Structured ("modular crypt format") hashes are unambiguous — check first.
    if _BCRYPT_RE.match(value):
        return ["bcrypt"]
    if _ARGON2_RE.match(value):
        return ["argon2"]
    if _SHA512_CRYPT_RE.match(value):
        return ["sha512crypt ($6$)"]
    if _MD5_CRYPT_RE.match(value):
        return ["md5crypt ($1$)"]

    candidates: list[str] = []
    if _HEX_RE.match(value):
        for name, length in _HEX_HASHES:
            if len(value) == length:
                candidates.append(name)
    return candidates or ["unknown (no length/charset match)"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Identify a hash by shape.")
    parser.add_argument("value")
    args = parser.parse_args(argv)
    for name in identify(args.value):
        print(name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
