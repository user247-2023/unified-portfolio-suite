"""Offline tests for the monitoring core (stdlib unittest).

    python -m unittest discover -s tests -v
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from collector.core import (  # noqa: E402
    AlertConfig, RollingLatency, classify, evaluate_alerts,
)


class ClassifyTests(unittest.TestCase):
    def test_down_has_no_latency(self):
        r = classify("gw", "10.0.0.1", connected=False, latency_s=0.1)
        self.assertFalse(r.up)
        self.assertIsNone(r.latency_s)   # invariant enforced

    def test_up_keeps_latency(self):
        r = classify("gw", "10.0.0.1", connected=True, latency_s=0.02)
        self.assertTrue(r.up)
        self.assertEqual(r.latency_s, 0.02)


class RollingLatencyTests(unittest.TestCase):
    def test_average(self):
        roll = RollingLatency(window=10)
        for v in (0.1, 0.2, 0.3):
            roll.add(v)
        self.assertAlmostEqual(roll.average(), 0.2)

    def test_ignores_none(self):
        roll = RollingLatency()
        roll.add(None)
        self.assertIsNone(roll.average())
        self.assertEqual(roll.count(), 0)

    def test_window_bounded(self):
        roll = RollingLatency(window=2)
        for v in (1.0, 2.0, 3.0):
            roll.add(v)
        self.assertEqual(roll.count(), 2)        # oldest dropped
        self.assertAlmostEqual(roll.average(), 2.5)


class AlertTests(unittest.TestCase):
    def test_down_alerts(self):
        r = classify("api", "h", connected=False, latency_s=None)
        alerts = evaluate_alerts(r, AlertConfig())
        self.assertTrue(any("DOWN" in a for a in alerts))

    def test_slow_alerts(self):
        r = classify("api", "h", connected=True, latency_s=0.8)
        alerts = evaluate_alerts(r, AlertConfig(latency_warn_s=0.5))
        self.assertTrue(any("SLOW" in a for a in alerts))

    def test_healthy_no_alerts(self):
        r = classify("api", "h", connected=True, latency_s=0.05)
        self.assertEqual(evaluate_alerts(r, AlertConfig(latency_warn_s=0.5)), [])


if __name__ == "__main__":
    unittest.main()
