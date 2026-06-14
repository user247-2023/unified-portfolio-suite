"""Shared domain layer for the AI-Powered SOC Platform.

Deliberately dependency-free (stdlib only) so the core models and the
correlation/triage logic can be imported and unit-tested without installing
FastAPI, Kafka clients, or ML libraries. The services build their I/O edges on
top of these types.
"""

from .models import Alert, Event, Incident, Priority, Severity

__all__ = ["Alert", "Event", "Incident", "Priority", "Severity"]
__version__ = "0.1.0"
