"""CLI entry point for the Security Audit Toolkit.

Purpose: Discover registered checks and run them against a target, emitting a
human report or JSON. Enforces an explicit authorization gate for network
targets.

Security trade-off: We require `--i-am-authorized` for any non-local target so
that running a scan is always a deliberate, attributable act. JSON output and a
configurable severity threshold let CI fail builds on real findings.
"""
from __future__ import annotations

import json
import sys

import click
from rich.console import Console
from rich.table import Table

from . import checks as _checks  # noqa: F401  (populates the registry)
from .core import Finding, Severity, registry

console = Console()


def _is_network_target(target: str) -> bool:
    return target.startswith(("http://", "https://"))


@click.group()
def cli() -> None:
    """Defensive, read-only security audit toolkit. Authorized use only."""


@cli.command("list")
def list_checks() -> None:
    """List available checks."""
    table = Table(title="Available checks")
    table.add_column("name", style="bold")
    table.add_column("description")
    for check in registry.all():
        table.add_row(check.name, check.description)
    console.print(table)


@cli.command("run")
@click.option("--target", required=True, help="URL or local path to audit.")
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
    findings: list[Finding] = []
    for check in checks:
        findings.extend(check.run(target))

    if fmt == "json":
        console.print_json(json.dumps([
            {**f.__dict__, "severity": f.severity.name} for f in findings
        ]))
    else:
        _print_report(findings)

    threshold = Severity[fail_on]
    if any(f.severity >= threshold for f in findings):
        sys.exit(2)


def _print_report(findings: list[Finding]) -> None:
    table = Table(title="Audit findings")
    table.add_column("severity")
    table.add_column("check")
    table.add_column("title")
    table.add_column("remediation")
    for f in sorted(findings, key=lambda x: x.severity, reverse=True):
        table.add_row(f.severity.name, f.check, f.title, f.remediation)
    console.print(table)


if __name__ == "__main__":
    cli()
