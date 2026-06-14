"""Multi-format encoder/decoder helper.

Purpose: A small, dependency-light CTF/analysis utility for the constant
encode/decode shuffling (base64, hex, URL, ROT13). Defensive/analysis tool —
nothing here attacks a system; it just transforms strings.

Usage:
    python tools/encoder.py b64encode "hello"
    python tools/encoder.py hexdecode 68656c6c6f
"""
from __future__ import annotations

import argparse
import base64
import codecs
import sys
import urllib.parse


def b64encode(s: str) -> str:
    return base64.b64encode(s.encode()).decode()


def b64decode(s: str) -> str:
    # Validate (defensive): reject non-base64 instead of returning garbage.
    return base64.b64decode(s, validate=True).decode("utf-8", errors="replace")


def hexencode(s: str) -> str:
    return s.encode().hex()


def hexdecode(s: str) -> str:
    return bytes.fromhex(s).decode("utf-8", errors="replace")


def urlencode(s: str) -> str:
    return urllib.parse.quote(s)


def urldecode(s: str) -> str:
    return urllib.parse.unquote(s)


def rot13(s: str) -> str:
    return codecs.encode(s, "rot_13")


_OPS = {
    "b64encode": b64encode, "b64decode": b64decode,
    "hexencode": hexencode, "hexdecode": hexdecode,
    "urlencode": urlencode, "urldecode": urldecode,
    "rot13": rot13,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CTF encode/decode helper.")
    parser.add_argument("op", choices=sorted(_OPS))
    parser.add_argument("value")
    args = parser.parse_args(argv)
    try:
        print(_OPS[args.op](args.value))
    except (ValueError, UnicodeDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
