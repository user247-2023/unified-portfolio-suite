"""Offline demo driver for the SOC pipeline.

Purpose: Feed a realistic attack scenario through the FULL pipeline
(normalize -> enrich -> correlate -> triage) and print the resulting incidents
as JSON — no Docker, no API, no third-party packages required.

Run from the project root:
    python seed_demo.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Make `shared` / `services` importable when run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from services.ingestion.app.pipeline import Pipeline  # noqa: E402


def main() -> None:
    pipeline = Pipeline()

    # Scenario: an external host brute-forces root over SSH, then succeeds.
    # (A genuinely public IP so enrichment tags it "external".)
    attacker = "45.9.148.99"
    events = [{"src_ip": attacker, "user": "root", "outcome": "failure",
               "host": "bastion"} for _ in range(6)]
    events.append({"src_ip": attacker, "user": "root", "outcome": "success",
                   "host": "bastion"})

    result = pipeline.process("sshd", events)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
