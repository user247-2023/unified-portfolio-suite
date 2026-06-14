"""XOR helpers.

Purpose: Classic CTF crypto utilities — XOR a buffer against a repeating key,
and brute-force a single-byte XOR key by scoring candidate plaintexts for
English-like printability. Pure stdlib, operates on local data only.

Usage:
    python tools/xor.py single 1b1b1b... (hex)
"""
from __future__ import annotations

import argparse

# Frequency-ish scoring: reward common English letters/space, penalize non-print.
_COMMON = b"ETAOIN SHRDLU etaoin shrdlu"


def repeating_key_xor(data: bytes, key: bytes) -> bytes:
    if not key:
        raise ValueError("key must be non-empty")
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def _score(text: bytes) -> int:
    score = 0
    for byte in text:
        if byte in _COMMON:
            score += 2
        elif 32 <= byte <= 126:   # other printable ASCII
            score += 1
        else:
            score -= 5            # non-printable: probably wrong key
    return score


def single_byte_xor_bruteforce(data: bytes) -> tuple[int, bytes, int]:
    """Return (best_key, best_plaintext, best_score) over all 256 byte keys."""
    best = (0, b"", -10**9)
    for key in range(256):
        candidate = bytes(b ^ key for b in data)
        s = _score(candidate)
        if s > best[2]:
            best = (key, candidate, s)
    return best


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="XOR helpers for CTF.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_single = sub.add_parser("single", help="single-byte XOR brute force")
    p_single.add_argument("hexdata", help="ciphertext as hex")

    p_rep = sub.add_parser("repeat", help="repeating-key XOR")
    p_rep.add_argument("hexdata")
    p_rep.add_argument("key", help="key as utf-8 text")

    args = parser.parse_args(argv)
    data = bytes.fromhex(args.hexdata)

    if args.cmd == "single":
        key, plaintext, score = single_byte_xor_bruteforce(data)
        print(f"key=0x{key:02x} score={score}")
        print("plaintext:", plaintext.decode("utf-8", errors="replace"))
    else:
        out = repeating_key_xor(data, args.key.encode())
        print(out.hex())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
