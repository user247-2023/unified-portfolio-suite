"""Security Audit Toolkit.

A defensive, read-only auditing toolkit. See README.md for authorized-use terms.
The public surface is intentionally small: the `Check`/`Finding` contract and a
registry that the CLI uses to discover checks.
"""

from .core import Check, Finding, Severity, registry

__all__ = ["Check", "Finding", "Severity", "registry"]
__version__ = "0.1.0"
