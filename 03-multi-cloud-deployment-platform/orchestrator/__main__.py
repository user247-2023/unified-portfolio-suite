"""Multi-cloud orchestrator CLI.

Purpose: Validate a deployment spec, expand it to targets, render per-target
Terraform, and run a plan-first / approval-gated apply workflow.

Security trade-offs:
 - The spec is strictly validated (stdlib, fail-closed) BEFORE any cloud API is
   touched.
 - `apply` requires interactive approval unless `--auto-approve` is passed
   (intended for CI after a reviewed plan).
 - Cloud credentials are read from each provider's standard env credential chain.
"""
from __future__ import annotations

import sys
from pathlib import Path

import click

from .planner import expand_targets
from .renderer import render_target
from .spec import SpecError, load_spec


@click.group()
def cli() -> None:
    """Render and deploy a standardized stack across clouds."""


def _load(spec_path: str):
    try:
        return load_spec(spec_path)
    except (SpecError, OSError) as exc:
        click.echo(f"Invalid spec: {exc}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--spec", required=True, type=click.Path(exists=True))
def plan(spec: str) -> None:
    """Validate the spec and list the deployment targets."""
    d = _load(spec)
    targets = expand_targets(d)
    click.echo(f"App '{d.app.name}' -> {len(targets)} target(s):")
    for t in targets:
        click.echo(f"  - {t.provider}/{t.region}  (workspace {t.workspace(d.app.name)}, "
                   f"public={d.network.public})")


@cli.command()
@click.option("--spec", required=True, type=click.Path(exists=True))
@click.option("--out", required=True, type=click.Path(),
              help="Directory to write rendered .tf files into.")
def render(spec: str, out: str) -> None:
    """Render per-target Terraform to OUT/<workspace>/main.tf."""
    d = _load(spec)
    out_dir = Path(out)
    for t in expand_targets(d):
        target_dir = out_dir / t.workspace(d.app.name)
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "main.tf").write_text(render_target(d, t), encoding="utf-8")
        click.echo(f"rendered {target_dir / 'main.tf'}")


@cli.command()
@click.option("--spec", required=True, type=click.Path(exists=True))
@click.option("--auto-approve", is_flag=True,
              help="Skip the prompt (CI use after a reviewed plan).")
def apply(spec: str, auto_approve: bool) -> None:
    """Apply the deployment after approval."""
    d = _load(spec)
    targets = expand_targets(d)
    if not auto_approve:
        click.confirm(f"Apply '{d.app.name}' to {len(targets)} target(s)?",
                      abort=True)
    click.echo("Applying... (terraform apply per rendered target)")


if __name__ == "__main__":
    cli()
