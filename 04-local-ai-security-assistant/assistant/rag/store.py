"""Offline vector store + retriever.

Purpose: Provide a dependency-free retrieval path so the RAG pipeline runs (and
is unit-testable) WITHOUT faiss, sentence-transformers, or a running model. A
deterministic hashing embedder maps text to a fixed-dimension vector; the store
ranks chunks by cosine similarity.

Trade-off: the hashing embedder is a lightweight stand-in (bag-of-words feature
hashing), not a semantic transformer. It is good enough for tests, demos, and
keyword-ish retrieval, and the `Retriever` interface is identical to what a real
embedder plugs into — so swapping in sentence-transformers later changes one
class, not the pipeline. All computation is local (privacy-preserving).
"""
from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass, field

from .pipeline import Chunk

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class HashingEmbedder:
    """Deterministic, local bag-of-words feature-hashing embedder."""

    def __init__(self, dim: int = 256) -> None:
        self.dim = dim

    def embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for token in _TOKEN_RE.findall(text.lower()):
            # Stable hash -> bucket. (hashlib, not built-in hash(), for
            # determinism across processes/runs.)
            h = int(hashlib.md5(token.encode()).hexdigest(), 16)
            vec[h % self.dim] += 1.0
        return _l2_normalize(vec)


def _l2_normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        return vec
    return [v / norm for v in vec]


def _cosine(a: list[float], b: list[float]) -> float:
    # Vectors are L2-normalized, so cosine == dot product.
    return sum(x * y for x, y in zip(a, b))


@dataclass
class VectorStore:
    embedder: HashingEmbedder = field(default_factory=HashingEmbedder)
    _items: list[tuple[Chunk, list[float]]] = field(default_factory=list)

    def add(self, chunks: list[Chunk]) -> None:
        for chunk in chunks:
            self._items.append((chunk, self.embedder.embed(chunk.text)))

    def search(self, query: str, k: int = 3) -> list[Chunk]:
        if not self._items:
            return []
        qv = self.embedder.embed(query)
        ranked = sorted(
            self._items, key=lambda item: _cosine(qv, item[1]), reverse=True
        )
        return [chunk for chunk, _ in ranked[:k]]

    def __len__(self) -> int:
        return len(self._items)


class Retriever:
    """Convenience wrapper: index chunks, then retrieve for a query."""

    def __init__(self, dim: int = 256) -> None:
        self.store = VectorStore(embedder=HashingEmbedder(dim=dim))

    def index(self, chunks: list[Chunk]) -> "Retriever":
        self.store.add(chunks)
        return self

    def retrieve(self, query: str, k: int = 3) -> list[Chunk]:
        return self.store.search(query, k)
