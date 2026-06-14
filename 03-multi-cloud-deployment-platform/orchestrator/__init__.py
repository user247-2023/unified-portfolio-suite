"""Multi-cloud deployment orchestrator.

The core (spec validation, target planning, HCL rendering) is dependency-free
(stdlib only) so it can be unit-tested without installing anything. PyYAML is
imported lazily only when loading a spec from a file; Click only for the CLI.
"""

from .spec import (
    AppSpec,
    DeploymentSpec,
    NetworkSpec,
    ProviderSpec,
    SpecError,
)
from .planner import Target, expand_targets
from .renderer import render_target

__all__ = [
    "AppSpec", "DeploymentSpec", "NetworkSpec", "ProviderSpec", "SpecError",
    "Target", "expand_targets", "render_target",
]
