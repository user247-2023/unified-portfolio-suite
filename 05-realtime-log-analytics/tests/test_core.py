"""Offline tests for the stream-processing core (stdlib unittest).

    python -m unittest discover -s tests -v
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from processing.core import Batcher, parse_event  # noqa: E402


class ParseEventTests(unittest.TestCase):
    def test_valid_event(self):
        raw = json.dumps({"ts": 1700000000.0, "service": "api",
                          "level": "ERROR", "message": "db timeout"})
        e = parse_event(raw)
        self.assertEqual(e.service, "api")
        self.assertEqual(e.level, "ERROR")

    def test_missing_required_field_raises(self):
        with self.assertRaises(ValueError):
            parse_event(json.dumps({"service": "api"}))  # no ts/message

    def test_invalid_json_raises(self):
        with self.assertRaises(ValueError):
            parse_event("{not json")

    def test_non_object_raises(self):
        with self.assertRaises(ValueError):
            parse_event(json.dumps([1, 2, 3]))

    def test_oversized_message_truncated(self):
        raw = json.dumps({"ts": 1.0, "service": "api", "message": "x" * 20000})
        self.assertLessEqual(len(parse_event(raw).message), 8192)

    def test_default_level_is_info(self):
        raw = json.dumps({"ts": 1.0, "service": "api", "message": "ok"})
        self.assertEqual(parse_event(raw).level, "INFO")


class BatcherTests(unittest.TestCase):
    def test_flushes_on_size(self):
        b = Batcher(max_size=3, max_interval=999, clock=lambda: 0.0)
        self.assertIsNone(b.add("a"))
        self.assertIsNone(b.add("b"))
        self.assertEqual(b.add("c"), ["a", "b", "c"])
        self.assertEqual(b.pending(), 0)

    def test_flushes_on_interval(self):
        now = {"t": 0.0}
        b = Batcher(max_size=999, max_interval=2.0, clock=lambda: now["t"])
        b.add("a")
        self.assertIsNone(b.tick())   # interval not elapsed
        now["t"] = 2.5
        self.assertEqual(b.tick(), ["a"])

    def test_tick_noop_when_empty(self):
        now = {"t": 0.0}
        b = Batcher(max_size=10, max_interval=1.0, clock=lambda: now["t"])
        now["t"] = 100.0
        self.assertIsNone(b.tick())   # nothing buffered -> no empty batch

    def test_force_flush(self):
        b = Batcher(max_size=10, clock=lambda: 0.0)
        b.add("x")
        self.assertEqual(b.flush(), ["x"])


if __name__ == "__main__":
    unittest.main()
