"""Offline tests for the RAG core (stdlib unittest — no faiss/ollama needed).

    python -m unittest discover -s tests -v
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from assistant.rag.pipeline import Chunk, build_prompt, chunk_text, discover_documents  # noqa: E402
from assistant.rag.store import HashingEmbedder, Retriever  # noqa: E402


class ChunkingTests(unittest.TestCase):
    def test_chunk_overlap_and_coverage(self):
        text = "x" * 2000
        chunks = chunk_text(text, source="t", size=800, overlap=100)
        self.assertGreaterEqual(len(chunks), 2)
        # Every chunk carries its source.
        self.assertTrue(all(c.source == "t" for c in chunks))

    def test_secret_files_skipped(self, ):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            (base / "notes.md").write_text("safe content", encoding="utf-8")
            (base / "id_rsa.key").write_text("PRIVATE", encoding="utf-8")
            (base / ".env").write_text("SECRET=1", encoding="utf-8")
            found = {p.name for p in discover_documents(str(base))}
        self.assertIn("notes.md", found)
        self.assertNotIn("id_rsa.key", found)
        self.assertNotIn(".env", found)


class EmbedderTests(unittest.TestCase):
    def test_deterministic(self):
        e = HashingEmbedder(dim=64)
        self.assertEqual(e.embed("hello world"), e.embed("hello world"))

    def test_normalized(self):
        e = HashingEmbedder(dim=64)
        v = e.embed("incident response runbook")
        norm = sum(x * x for x in v) ** 0.5
        self.assertAlmostEqual(norm, 1.0, places=6)


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.docs = [
            Chunk(source="phishing.md",
                  text="If a user reports a phishing email, isolate the mailbox "
                       "and reset credentials."),
            Chunk(source="backups.md",
                  text="Verify nightly database backups complete and test restores."),
            Chunk(source="patching.md",
                  text="Apply critical OS patches within 72 hours of release."),
        ]
        self.retriever = Retriever().index(self.docs)

    def test_relevant_chunk_ranked_first(self):
        results = self.retriever.retrieve("how do we handle a phishing report?", k=1)
        self.assertEqual(results[0].source, "phishing.md")

    def test_k_limits_results(self):
        self.assertEqual(len(self.retriever.retrieve("patches", k=2)), 2)

    def test_empty_store_returns_empty(self):
        self.assertEqual(Retriever().retrieve("anything"), [])


class PromptTests(unittest.TestCase):
    def test_prompt_includes_sources_and_question(self):
        ctx = [Chunk(source="runbook.md", text="reset credentials")]
        prompt = build_prompt("what to do?", ctx)
        self.assertIn("runbook.md", prompt)
        self.assertIn("what to do?", prompt)
        self.assertIn("defensive security assistant", prompt.lower())


if __name__ == "__main__":
    unittest.main()
