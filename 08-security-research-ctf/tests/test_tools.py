"""Tests for the CTF/analysis tools (stdlib unittest — no installs needed).

    python -m unittest discover -s tests -v
"""
import base64
import json
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import encoder, hashid, jwt_tool, xor  # noqa: E402


class EncoderTests(unittest.TestCase):
    def test_b64_roundtrip(self):
        self.assertEqual(encoder.b64decode(encoder.b64encode("hello")), "hello")

    def test_hex_roundtrip(self):
        self.assertEqual(encoder.hexdecode(encoder.hexencode("hi")), "hi")

    def test_rot13_involution(self):
        self.assertEqual(encoder.rot13(encoder.rot13("Secret")), "Secret")


class HashIdTests(unittest.TestCase):
    def test_md5_length(self):
        self.assertIn("MD5", hashid.identify("5f4dcc3b5aa765d61d8327deb882cf99"))

    def test_sha256_length(self):
        self.assertIn("SHA-256", hashid.identify("a" * 64))

    def test_bcrypt_pattern(self):
        h = "$2b$12$" + "a" * 53
        self.assertEqual(hashid.identify(h), ["bcrypt"])

    def test_unknown(self):
        self.assertEqual(hashid.identify("xyz"), ["unknown (no length/charset match)"])


class JwtTests(unittest.TestCase):
    def _make_token(self, header, payload):
        def seg(d):
            return base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=").decode()
        return f"{seg(header)}.{seg(payload)}.sig"

    def test_decode_roundtrip(self):
        tok = self._make_token({"alg": "HS256"}, {"sub": "abc", "exp": 9999999999})
        header, payload = jwt_tool.decode(tok)
        self.assertEqual(header["alg"], "HS256")
        self.assertEqual(payload["sub"], "abc")

    def test_alg_none_flagged(self):
        tok = self._make_token({"alg": "none"}, {"sub": "x"})
        header, payload = jwt_tool.decode(tok)
        warnings = jwt_tool.analyze(header, payload)
        self.assertTrue(any("alg=none" in w for w in warnings))

    def test_expired_flagged(self):
        tok = self._make_token({"alg": "HS256"}, {"exp": 100})
        header, payload = jwt_tool.decode(tok)
        warnings = jwt_tool.analyze(header, payload, now=int(time.time()))
        self.assertTrue(any("expired" in w for w in warnings))

    def test_malformed_rejected(self):
        with self.assertRaises(ValueError):
            jwt_tool.decode("not-a-jwt")


class XorTests(unittest.TestCase):
    def test_repeating_key_roundtrip(self):
        data = b"attack at dawn"
        ct = xor.repeating_key_xor(data, b"KEY")
        self.assertEqual(xor.repeating_key_xor(ct, b"KEY"), data)

    def test_single_byte_bruteforce_recovers_key(self):
        plaintext = b"The quick brown fox jumps over the lazy dog."
        key = 0x42
        ct = bytes(b ^ key for b in plaintext)
        found_key, recovered, _ = xor.single_byte_xor_bruteforce(ct)
        self.assertEqual(found_key, key)
        self.assertEqual(recovered, plaintext)


if __name__ == "__main__":
    unittest.main()
