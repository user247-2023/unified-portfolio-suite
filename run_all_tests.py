#!/usr/bin/env python3
"""Top-level test runner for the Unified Portfolio Suite.

Purpose: Run every project's test suite from a single command, on any OS, and
print a consolidated pass/fail summary. Mirrors what CI does locally.

Design: each project's core is dependency-free, so the Python suites run with
`python -m unittest` and Project 01 with `node --test` — no installs required.
Project 06 (C) is run via `make test` only if a C compiler + make are present;
otherwise it is reported as SKIPPED (it is covered in CI).

Usage:
    python run_all_tests.py
Exit code is non-zero if any suite fails (so it can gate a pre-push hook).
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# (label, working dir, command). Commands are chosen to need no pip installs.
PY_PROJECTS = [
    "02-security-audit-toolkit",
    "03-multi-cloud-deployment-platform",
    "04-local-ai-security-assistant",
    "05-realtime-log-analytics",
    "07-network-monitoring-suite",
    "08-security-research-ctf",
    "09-ai-powered-soc-platform",
]

GREEN, RED, YELLOW, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[0m"


def _run(label: str, cwd: Path, cmd: list[str]) -> str:
    """Run a suite; return 'PASS' | 'FAIL' | 'SKIP'."""
    print(f"\n=== {label} ===")
    try:
        proc = subprocess.run(cmd, cwd=cwd, text=True)
    except FileNotFoundError:
        print(f"{YELLOW}SKIP (command not found: {cmd[0]}){RESET}")
        return "SKIP"
    return "PASS" if proc.returncode == 0 else "FAIL"


def main() -> int:
    results: dict[str, str] = {}

    # Python projects (stdlib unittest).
    for proj in PY_PROJECTS:
        results[proj] = _run(
            proj, ROOT / proj,
            [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        )

    # Project 01 — Node built-in test runner.
    if shutil.which("node"):
        results["01-enterprise-asset-management"] = _run(
            "01-enterprise-asset-management",
            ROOT / "01-enterprise-asset-management" / "backend",
            ["node", "--test"],
        )
    else:
        results["01-enterprise-asset-management"] = "SKIP"

    # Project 06 — C, only if a toolchain is available locally.
    if shutil.which("make") and (shutil.which("cc") or shutil.which("gcc")):
        results["06-mini-os-components"] = _run(
            "06-mini-os-components", ROOT / "06-mini-os-components",
            ["make", "test"],
        )
    else:
        print("\n=== 06-mini-os-components ===")
        print(f"{YELLOW}SKIP (no C toolchain locally; covered in CI){RESET}")
        results["06-mini-os-components"] = "SKIP"

    # Summary.
    print("\n" + "=" * 48)
    print("SUMMARY")
    print("=" * 48)
    for proj in sorted(results):
        status = results[proj]
        color = {"PASS": GREEN, "FAIL": RED, "SKIP": YELLOW}[status]
        print(f"  {color}{status:4}{RESET}  {proj}")

    failed = [p for p, s in results.items() if s == "FAIL"]
    print()
    if failed:
        print(f"{RED}{len(failed)} suite(s) FAILED: {', '.join(failed)}{RESET}")
        return 1
    print(f"{GREEN}All runnable suites passed.{RESET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
