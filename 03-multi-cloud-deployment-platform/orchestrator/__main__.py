"""Multi-cloud orchestrator CLI.

Purpose: Validate a deployment spec, render provider-specific Terraform, and run
a plan-first / approval-gated apply workflow.

Security trade-offs:
 - The spec is validated with Pydantic BEFORE any cloud API is touched
   (fail-closed on malformed input).
 - `apply` requires interactive approval unless `--auto-approve` is passed
   (intended for CI where the plan was reviewed in a prior step).
 - Cloud credentials are read from the provider's standard env credential chain,
   never from the spec or CLI args.
"""
from __future__ import annotations

import sys
from pathlib import Path

import click
import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator


class ProviderSpec(BaseModel):
    name: str
    regions: list[str] = Field(min_length=1)

    @field_validator("name")
    @classmethod
    def known_provider(cls, v: str) -> str:
        if v not in {"aws", "gcp", "azure"}:
            raise ValueError(f"unsupported provider: {v}")
        return v


class AppSpec(BaseModel):
    name: str
    image: str
    port: int = Field(ge=1, le=65535)
    replicas: int = Field(ge=1, le=100)


class NetworkSpec(BaseModel):
    cidr: str
    public: bool = False  # fail-closed: private by default


class DeploymentSpec(BaseModel):
    app: AppSpec
    providers: list[ProviderSpec] = Field(min_length=1)
    network: NetworkSpec


def load_spec(path: str) -> DeploymentSpec:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return DeploymentSpec.model_validate(raw)


@click.group()
def cli() -> None:
    """Render and deploy a standardized stack across clouds."""


@cli.command()
@click.option("--spec", required=True, type=click.Path(exists=True))
def plan(spec: str) -> None:
    """Validate the spec and show what would be deployed (terraform plan)."""
    try:
        d = load_spec(spec)
    except (ValidationError, yaml.YAMLError) as exc:
        click.echo(f"Invalid spec: {exc}", err=True)
        sys.exit(1)
    targets = [(p.name, r) for p in d.providers for r in p.regions]
    click.echo(f"App '{d.app.name}' -> {len(targets)} target(s):")
    for provider, region in targets:
        click.echo(f"  - terraform plan: {provider}/{region} "
                   f"(public={d.network.public})")
    click.echo("Run `apply` to provision (you will be asked to confirm).")


@cli.command()
@click.option("--spec", required=True, type=click.Path(exists=True))
@click.option("--auto-approve", is_flag=True,
              help="Skip the interactive prompt (CI use after reviewed plan).")
def apply(spec: str, auto_approve: bool) -> None:
    """Apply the deployment after approval."""
    d = load_spec(spec)
    if not auto_approve:
        click.confirm(
            f"Apply '{d.app.name}' to {len(d.providers)} provider(s)?",
            abort=True,
        )
    # In a full implementation this shells out to `terraform apply` per target.
    click.echo("Applying... (terraform apply per rendered target)")


if __name__ == "__main__":
    cli()
