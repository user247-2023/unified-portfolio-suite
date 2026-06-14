"""Offline tests for the Security Audit Toolkit.

These run with NO third-party packages (httpx/click not required) because the
check evaluation logic and reporting are pure stdlib:

    python -m unittest discover -s tests -v
"""
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from audit_toolkit import registry, Severity  # noqa: E402
import audit_toolkit.checks  # noqa: F401,E402  (populate registry)
from audit_toolkit import report  # noqa: E402
from audit_toolkit.checks.http_headers import evaluate_headers  # noqa: E402
from audit_toolkit.checks.tls_cert import evaluate_validity  # noqa: E402


class RegistryTests(unittest.TestCase):
    def test_discovers_all_checks(self):
        names = {c.name for c in registry.all()}
        self.assertTrue({"http-headers", "file-permissions", "tls-cert"} <= names)


class HttpHeaderEvalTests(unittest.TestCase):
    def test_missing_hsts_is_high(self):
        findings = evaluate_headers({"content-security-policy": "default-src 'self'"})
        titles = {f.title for f in findings}
        self.assertIn("Missing header: strict-transport-security", titles)
        hsts = next(f for f in findings if "strict-transport" in f.title)
        self.assertEqual(hsts.severity, Severity.HIGH)

    def test_all_present_is_info(self):
        headers = {
            "strict-transport-security": "max-age=1",
            "content-security-policy": "x",
            "x-content-type-options": "nosniff",
            "x-frame-options": "DENY",
            "referrer-policy": "no-referrer",
        }
        findings = evaluate_headers(headers, 200)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].severity, Severity.INFO)


class TlsEvalTests(unittest.TestCase):
    def test_expired_is_critical(self):
        now = time.time()
        findings = evaluate_validity(now - 86400, now)
        self.assertEqual(findings[0].severity, Severity.CRITICAL)

    def test_expiring_soon_is_high(self):
        now = time.time()
        findings = evaluate_validity(now + 5 * 86400, now)
        self.assertEqual(findings[0].severity, Severity.HIGH)

    def test_healthy_is_info(self):
        now = time.time()
        findings = evaluate_validity(now + 200 * 86400, now)
        self.assertEqual(findings[0].severity, Severity.INFO)


class FilePermsTests(unittest.TestCase):
    def test_runs_clean_on_empty_dir(self, ):
        check = registry.get("file-permissions")
        findings = check.run(str(Path(__file__).parent))
        self.assertTrue(findings)
        self.assertTrue(all(f.check == "file-permissions" for f in findings))


class ReportTests(unittest.TestCase):
    def test_exit_code_gates_on_threshold(self):
        check = registry.get("file-permissions")
        info_findings = check.run(str(Path(__file__).parent))
        self.assertEqual(report.exit_code(info_findings, Severity.HIGH), 0)

    def test_json_is_parseable_and_redacted_shape(self):
        import json
        findings = evaluate_headers({}, 200)
        data = json.loads(report.to_json(findings))
        self.assertIsInstance(data, list)
        self.assertIn("severity", data[0])


if __name__ == "__main__":
    unittest.main()
