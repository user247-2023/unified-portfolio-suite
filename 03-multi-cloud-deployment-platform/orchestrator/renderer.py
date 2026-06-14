"""Terraform (HCL) renderer.

Purpose: Render provider-agnostic HCL for a single deployment target from the
shared module interface. Uses stdlib `string.Template` (no Jinja dependency) so
rendering is deterministic and unit-testable offline.

Security note: the rendered config wires `network.public` straight through from
the validated spec (which defaults to false), so a target is private unless the
spec explicitly opted in. No secrets are emitted — provider auth is supplied by
the environment at `terraform apply` time.
"""
from __future__ import annotations

from string import Template

from .planner import Target
from .spec import DeploymentSpec

_TEMPLATE = Template(
    '# AUTO-GENERATED for ${workspace}. Do not edit by hand.\n'
    'terraform {\n'
    '  required_version = ">= 1.5"\n'
    '}\n\n'
    'provider "${provider}" {\n'
    '  region = "${region}"\n'
    '}\n\n'
    'module "network" {\n'
    '  source = "../../terraform/modules/network"\n'
    '  name   = "${app_name}"\n'
    '  cidr   = "${cidr}"\n'
    '  public = ${public}\n'
    '}\n\n'
    'module "app" {\n'
    '  source    = "../../terraform/modules/app"\n'
    '  name      = "${app_name}"\n'
    '  image     = "${image}"\n'
    '  port      = ${port}\n'
    '  replicas  = ${replicas}\n'
    '  subnet_id = module.network.subnet_id\n'
    '}\n'
)


def render_target(spec: DeploymentSpec, target: Target) -> str:
    """Render the HCL for one (provider, region) target."""
    return _TEMPLATE.substitute(
        workspace=target.workspace(spec.app.name),
        provider=target.provider,
        region=target.region,
        app_name=spec.app.name,
        image=spec.app.image,
        port=spec.app.port,
        replicas=spec.app.replicas,
        cidr=spec.network.cidr,
        public="true" if spec.network.public else "false",
    )
