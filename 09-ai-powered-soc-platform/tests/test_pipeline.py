"""End-to-end tests for the SOC detection pipeline.

Purpose: Prove the core promise — that a burst of auth failures followed by a
success from an external IP becomes a high-priority, well-explained incident.
Uses stdlib `unittest` so it runs with NO third-party packages installed:

    python -m unittest discover -s tests -v
"""
import sys
import unittest
from pathlib import Path

# Make the platform root importable when run directly (mirrors conftest.py).
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.models import Priority, Severity  # noqa: E402
from services.correlation.app.engine import CorrelationEngine  # noqa: E402
from services.correlation.app.rules import RuleConfig  # noqa: E402
from services.ingestion.app.normalizer import normalize  # noqa: E402
from services.ingestion.app.enrichment import enrich  # noqa: E402
from services.triage.app.triage import triage  # noqa: E402


def _ssh_failure(ip, user="root"):
    return {"src_ip": ip, "user": user, "outcome": "failure", "host": "bastion"}


def _ssh_success(ip, user="root"):
    return {"src_ip": ip, "user": user, "outcome": "success", "host": "bastion"}


class NormalizerTests(unittest.TestCase):
    def test_sshd_failure_maps_to_auth_failure(self):
        e = normalize("sshd", _ssh_failure("203.0.113.9"))
        self.assertEqual(e.event_type, "auth_failure")
        self.assertEqual(e.src_ip, "203.0.113.9")

    def test_oversized_fields_are_truncated(self):
        e = normalize("sshd", {"user": "x" * 5000, "outcome": "failure"})
        self.assertLessEqual(len(e.user), 255)

    def test_bad_payload_rejected(self):
        with self.assertRaises(ValueError):
            normalize("sshd", ["not", "a", "dict"])  # type: ignore[arg-type]


class EnrichmentTests(unittest.TestCase):
    def test_external_ip_tagged(self):
        e = enrich(normalize("sshd", _ssh_failure("8.8.8.8")))
        self.assertEqual(e.attributes.get("src_scope"), "external")

    def test_internal_ip_tagged(self):
        e = enrich(normalize("sshd", _ssh_failure("10.0.0.5")))
        self.assertEqual(e.attributes.get("src_scope"), "internal")

    def test_secret_attribute_redacted(self):
        e = enrich(normalize("generic", {"attributes": {"password": "hunter2"}}))
        self.assertEqual(e.attributes.get("password"), "[REDACTED]")


class CorrelationTests(unittest.TestCase):
    def test_brute_force_fires_at_threshold(self):
        engine = CorrelationEngine(window_seconds=300,
                                   rule_config=RuleConfig(brute_force_threshold=5))
        alerts = []
        for _ in range(5):
            alerts += engine.ingest(enrich(normalize("sshd", _ssh_failure("203.0.113.9"))))
        rules = {a.rule for a in alerts}
        self.assertIn("brute_force", rules)

    def test_no_alert_below_threshold(self):
        engine = CorrelationEngine(rule_config=RuleConfig(brute_force_threshold=5))
        alerts = []
        for _ in range(3):
            alerts += engine.ingest(enrich(normalize("sshd", _ssh_failure("10.0.0.5"))))
        self.assertEqual(alerts, [])


class TriageEndToEndTests(unittest.TestCase):
    def test_successful_brute_force_becomes_p1_incident(self):
        engine = CorrelationEngine(rule_config=RuleConfig(brute_force_threshold=5))
        alerts = []
        # 6 failures then a success, all from an external IP against root.
        for _ in range(6):
            alerts += engine.ingest(enrich(normalize("sshd", _ssh_failure("203.0.113.9"))))
        alerts += engine.ingest(enrich(normalize("sshd", _ssh_success("203.0.113.9"))))

        incidents = triage(alerts, auto_escalate_score=80)
        self.assertTrue(incidents)
        top = incidents[0]
        # Critical detection + external + sensitive account => P1, high score.
        self.assertEqual(top.priority, Priority.P1)
        self.assertGreaterEqual(top.risk_score, 80)
        self.assertTrue(any("successful_brute_force" == a.rule for a in top.alerts))
        self.assertTrue(top.recommended_actions)   # playbook attached
        self.assertTrue(top.rationale)             # explainable


if __name__ == "__main__":
    unittest.main()
