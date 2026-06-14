# Security Research & CTF Repository

A structured, open-source home for capture-the-flag (CTF) writeups, security
research notes, and small defensive/analysis tools — built for learning and
sharing in the open.

> ⚠️ **Ethics & scope.** Everything here is for **education, CTF competitions,
> and authorized research**. Writeups cover challenges that are *designed* to be
> solved, or systems the author owns/has permission to test. Real-world findings
> follow [responsible disclosure](SECURITY.md).

## Problem

CTF and security learning is scattered across gists, blog posts, and screenshots
that rot. There's no consistent structure, so knowledge isn't reusable and
others can't easily learn from it. And without an explicit ethics/disclosure
policy, sharing security work risks being misread.

## Solution

- **A consistent writeup template** (`writeups/TEMPLATE.md`) so every challenge
  is documented the same way: category, recon, vulnerability, exploitation,
  remediation, and lessons.
- **A small tools/ folder** for reusable *defensive/analysis* helpers (encoders,
  parsers, hashing utilities) — not weaponized exploits.
- **A clear ethics + disclosure policy** so the repo's intent is unambiguous.

## Tech Stack

- **Markdown** — writeups and notes.
- **Python 3.12** — small analysis utilities (`tools/`).

## Usage

```bash
# Start a new writeup from the template:
cp writeups/TEMPLATE.md writeups/2026-some-ctf-challenge.md

# Analysis helpers (all stdlib — no install needed):
python tools/encoder.py b64encode "hello"
python tools/hashid.py 5f4dcc3b5aa765d61d8327deb882cf99      # -> MD5
python tools/jwt_tool.py eyJhbGciOiJub25lIn0.eyJzdWIiOiJ4In0.   # decode + flag alg=none
python tools/xor.py single 1e120d1f...                         # single-byte XOR brute

# Run the tool test suite (stdlib unittest):
python -m unittest discover -s tests -v
```

The `tools/` helpers are dependency-free; `pip install -r requirements.txt`
only adds `pwntools` for interactive CTF I/O against local/practice targets.

## Security Considerations

- **Defensive framing.** Writeups emphasize the *root cause* and *remediation*,
  not turnkey exploitation of live systems. Tools are analysis/encoding helpers,
  not exploit kits.
- **No live targets / no secrets.** Examples use intentionally-vulnerable
  practice targets. No real credentials, tokens, or PII are committed.
- **Responsible disclosure.** Any finding against a real system is reported
  privately per [SECURITY.md](SECURITY.md) before (if ever) being written up.

## Lessons Learned

- A fixed template made writeups comparable and far more useful as a study set.
- Leading every writeup with the *remediation* (not just the exploit) keeps the
  repo squarely educational/defensive.
- An explicit, up-front ethics policy removes ambiguity about why the work
  exists.
