"""Test bootstrap.

Puts the platform root on sys.path so `shared` and `services` import cleanly
whether tests are run via pytest or `python -m unittest`.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
