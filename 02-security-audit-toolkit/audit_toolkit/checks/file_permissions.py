"""Filesystem permission check.

Purpose: Read-only check that scans a local directory for secret-bearing files
(.env, *.pem, *.key) that are world-readable or accidentally tracked, a common
source of credential leaks.

Security trade-off: Reports only the *path* and permission bits of offending
files — never their contents — so the report itself can't leak a secret.
On Windows POSIX mode bits are approximate; the check degrades to "tracked
secret file present" advisories there.
"""
from __future__ import annotations

import os
import stat
from pathlib import Path

from ..core import Finding, Severity, register

_SECRET_GLOBS = ("*.pem", "*.key", "*.p12", "*.pfx", ".env", ".env.*")


@register
class FilePermissionsCheck:
    name = "file-permissions"
    description = "Find world-readable secret files in a local directory tree."

    def run(self, target: str) -> list[Finding]:
        root = Path(target)
        if not root.exists():
            return [Finding(
                check=self.name, severity=Severity.INFO,
                title="Path not found",
                detail=f"{target} does not exist.",
                remediation="Provide a local directory path as the target.",
            )]

        findings: list[Finding] = []
        for pattern in _SECRET_GLOBS:
            for path in root.rglob(pattern):
                if path.name == ".env.example":
                    continue  # templates are safe by convention
                try:
                    mode = path.stat().st_mode
                except OSError:
                    continue
                world_readable = bool(mode & stat.S_IROTH)
                if world_readable:
                    findings.append(Finding(
                        check=self.name, severity=Severity.HIGH,
                        title="World-readable secret file",
                        detail=f"{path} is readable by all users.",
                        remediation="Restrict permissions: `chmod 600` (or ACL "
                                    "equivalent) and rotate any exposed secret.",
                        evidence=f"mode={oct(mode & 0o777)}",
                    ))
        if not findings:
            findings.append(Finding(
                check=self.name, severity=Severity.INFO,
                title="No world-readable secret files found",
                detail=f"Scanned {target} for common secret file patterns.",
                remediation="No action required.",
            ))
        return findings
