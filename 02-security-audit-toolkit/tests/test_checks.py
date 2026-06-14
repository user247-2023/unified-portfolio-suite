"""Smoke tests for the Security Audit Toolkit.

Purpose: Verify the registry discovers checks and that the file-permissions
check runs read-only against a temp directory without raising.
"""
from audit_toolkit import registry
import audit_toolkit.checks  # noqa: F401  (populate registry)


def test_registry_discovers_checks():
    names = {c.name for c in registry.all()}
    assert {"http-headers", "file-permissions"} <= names


def test_file_permissions_check_runs(tmp_path):
    check = registry.get("file-permissions")
    findings = check.run(str(tmp_path))
    assert findings  # at least the "nothing found" INFO finding
    assert all(f.check == "file-permissions" for f in findings)
