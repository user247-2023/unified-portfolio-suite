"""Core contracts for the Security Audit Toolkit.

Purpose: Define the small, stable interface every check implements (`Check`)
and the structured result it returns (`Finding`), plus a registry so checks are
discovered rather than hardcoded into the runner.

Design/security trade-off: Findings are structured data, never pre-formatted
strings, so the same result can drive a human report AND a CI gate. Findings
carry only the *location/evidence* of an issue, never raw secret values.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Callable, Protocol, runtime_checkable


class Severity(enum.IntEnum):
    """Ordered so reports can sort/threshold numerically (CRITICAL highest)."""

    INFO = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass(frozen=True, slots=True)
class Finding:
    """A single audit result. Immutable so it can't be mutated after a check
    returns it. `evidence` must never contain a raw secret — only its presence
    or location."""

    check: str
    severity: Severity
    title: str
    detail: str
    remediation: str
    evidence: str = ""


@runtime_checkable
class Check(Protocol):
    """The contract every check implements. Intentionally tiny."""

    name: str
    description: str

    def run(self, target: str) -> list[Finding]:
        """Audit `target` and return findings. MUST be read-only."""
        ...


@dataclass
class _Registry:
    """Holds discovered checks. Checks register themselves at import time via
    the `@register` decorator, keeping the runner decoupled from concrete checks."""

    _checks: dict[str, Check] = field(default_factory=dict)

    def register(self, check: Check) -> Check:
        if check.name in self._checks:
            raise ValueError(f"duplicate check name: {check.name}")
        self._checks[check.name] = check
        return check

    def get(self, name: str) -> Check:
        if name not in self._checks:
            raise KeyError(f"unknown check: {name}")
        return self._checks[name]

    def all(self) -> list[Check]:
        return list(self._checks.values())


registry = _Registry()


def register(cls: type) -> type:
    """Class decorator: instantiate and register a check. Fail loudly if the
    class doesn't satisfy the `Check` protocol (defensive: bad plugins are
    caught at import, not at run time)."""
    instance = cls()
    if not isinstance(instance, Check):
        raise TypeError(f"{cls.__name__} does not satisfy the Check protocol")
    registry.register(instance)
    return cls
