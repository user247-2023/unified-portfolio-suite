"""Offline tests for the multi-cloud orchestrator core (stdlib unittest).

    python -m unittest discover -s tests -v
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from orchestrator import (  # noqa: E402
    DeploymentSpec, SpecError, expand_targets, render_target,
)

_VALID = {
    "app": {"name": "demo", "image": "ghcr.io/x/demo:1.0", "port": 8080, "replicas": 2},
    "providers": [
        {"name": "aws", "regions": ["eu-west-1", "us-east-1"]},
        {"name": "gcp", "regions": ["europe-west1"]},
    ],
    "network": {"cidr": "10.0.0.0/16", "public": False},
}


class SpecValidationTests(unittest.TestCase):
    def test_valid_spec_builds(self):
        spec = DeploymentSpec.from_dict(_VALID)
        self.assertEqual(spec.app.name, "demo")
        self.assertFalse(spec.network.public)

    def test_unknown_provider_rejected(self):
        bad = {**_VALID, "providers": [{"name": "oracle", "regions": ["x"]}]}
        with self.assertRaises(SpecError):
            DeploymentSpec.from_dict(bad)

    def test_port_out_of_range_rejected(self):
        bad = {**_VALID, "app": {**_VALID["app"], "port": 99999}}
        with self.assertRaises(SpecError):
            DeploymentSpec.from_dict(bad)

    def test_missing_field_rejected(self):
        with self.assertRaises(SpecError):
            DeploymentSpec.from_dict({"app": {"name": "x"}})

    def test_bool_not_accepted_as_port(self):
        bad = {**_VALID, "app": {**_VALID["app"], "port": True}}
        with self.assertRaises(SpecError):
            DeploymentSpec.from_dict(bad)


class PlannerTests(unittest.TestCase):
    def test_target_expansion_count_and_order(self):
        spec = DeploymentSpec.from_dict(_VALID)
        targets = expand_targets(spec)
        self.assertEqual(len(targets), 3)  # 2 aws + 1 gcp
        self.assertEqual(targets[0].provider, "aws")
        self.assertEqual(targets[0].workspace("demo"), "demo-aws-eu-west-1")


class RendererTests(unittest.TestCase):
    def test_render_contains_key_values(self):
        spec = DeploymentSpec.from_dict(_VALID)
        target = expand_targets(spec)[0]
        hcl = render_target(spec, target)
        self.assertIn('provider "aws"', hcl)
        self.assertIn('region = "eu-west-1"', hcl)
        self.assertIn('cidr   = "10.0.0.0/16"', hcl)
        self.assertIn("public = false", hcl)   # fail-closed default rendered

    def test_public_flag_propagates(self):
        spec = DeploymentSpec.from_dict({**_VALID, "network": {"cidr": "10.0.0.0/16", "public": True}})
        hcl = render_target(spec, expand_targets(spec)[0])
        self.assertIn("public = true", hcl)


if __name__ == "__main__":
    unittest.main()
