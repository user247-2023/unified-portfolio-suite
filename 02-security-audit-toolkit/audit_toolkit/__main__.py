"""CLI entry point for the Security Audit Toolkit.

Purpose: Discover registered checks and run them against a target, emitting a
human report or JSON. Enforces an explicit authorization gate for network
targets and a configurable severity threshold for CI gating.

Security trade-off: we require `--i-am-authorized` for any non-local target so
that running a scan is always a deliberate, attributable act. Rendering/exit-code
logic lives in `report.py` (stdlib) so it is testable without the CLI deps.
"""
from __future__ import annotations

import sys

import click

from . import checks as _checks  # noqa: F401  (populates the registry)
from . import report
from .core import Severity, registry


def _is_network_target(target: str) -> bool:
    return target.startswith(("http://", "https://")) or ":" in target.split("/")[0]


@click.group()
def cli() -> None:
    """Defensive, read-only security audit toolkit. Authorized use only."""


@cli.command("list")
def list_checks() -> None:
    """List available checks."""
    for check in registry.all():
        click.echo(f"{check.name:16} {check.description}")


@cli.command("run")
@click.option("--target", required=True, help="URL, host[:port], or local path.")
@click.option("--check", "check_name", default=None,
              help="Run a single check by name (default: all).")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]),
              default="text")
@click.option("--fail-on", type=click.Choice([s.name for s in Severity]),
              default="HIGH", help="Exit non-zero if a finding >= this severity.")
@click.option("--i-am-authorized", is_flag=True,
              help="Confirm you are authorized to assess this target.")
def run(target: str, check_name: str | None, fmt: str, fail_on: str,
        i_am_authorized: bool) -> None:
    """Run checks against TARGET."""
    if _is_network_target(target) and not i_am_authorized:
        raise click.UsageError(
            "Network target requires --i-am-authorized. Only assess systems you "
            "own or have written permission to test."
        )

    checks = [registry.get(check_name)] if check_name else registry.all()
    findings = [f for check in checks for f in check.run(target)]

    output = report.to_json(findings) if fmt == "json" else report.to_text(findings)
    click.echo(output)
    sys.exit(report.exit_code(findings, Severity[fail_on]))


if __name__ == "__main__":
    cli()
