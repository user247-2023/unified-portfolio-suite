"""Deployment planner.

Purpose: Expand a validated spec into the concrete list of (provider, region)
deployment targets the renderer/apply step will act on. Pure function — easy to
test and reason about.
"""
from __future__ import annotations

from dataclasses import dataclass

from .spec import DeploymentSpec


@dataclass(frozen=True)
class Target:
    provider: str
    region: str

    def workspace(self, app_name: str) -> str:
        """Stable Terraform workspace/state key for this target."""
        return f"{app_name}-{self.provider}-{self.region}"


def expand_targets(spec: DeploymentSpec) -> list[Target]:
    """One Target per (provider, region) pair, in deterministic order."""
    targets: list[Target] = []
    for provider in spec.providers:
        for region in provider.regions:
            targets.append(Target(provider=provider.name, region=region))
    return targets
