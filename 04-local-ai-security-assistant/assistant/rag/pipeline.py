"""RAG pipeline for the Local AI Security Assistant.

Purpose: Chunk + embed local security documents into a FAISS index, and answer
questions by retrieving relevant chunks and prompting a LOCAL Ollama model.

Security trade-offs:
 - The indexer skips secret-bearing files so credentials never enter the vector
   store (a vector DB is a data store like any other).
 - All network calls target the local Ollama host only; no external API is used.
 - Answers carry their source chunks (citations) to keep advice grounded/auditable.

Performance trade-off: a CPU FAISS flat index is simple and exact but O(n) per
query; for large corpora swap in an IVF/HNSW index (approximate, much faster).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# Files we refuse to index because they may contain secrets.
_SECRET_SUFFIXES = {".key", ".pem", ".p12", ".pfx"}
_SECRET_NAMES = {".env"}


@dataclass
class Chunk:
    source: str
    text: str


def discover_documents(root: str) -> list[Path]:
    """Return indexable text files under `root`, skipping secret-bearing ones."""
    paths: list[Path] = []
    for path in Path(root).rglob("*"):
        if not path.is_file():
            continue
        if path.suffix in _SECRET_SUFFIXES or path.name in _SECRET_NAMES:
            continue  # defensive: never embed secrets
        if path.suffix.lower() in {".md", ".txt", ".log", ".rst"}:
            paths.append(path)
    return paths


def chunk_text(text: str, source: str, size: int = 800, overlap: int = 100) -> list[Chunk]:
    """Split text into overlapping windows so retrieval has local context."""
    chunks: list[Chunk] = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(Chunk(source=source, text=text[start:end]))
        start = end - overlap
    return chunks


def build_prompt(question: str, contexts: list[Chunk]) -> str:
    """Compose a grounded, defensive-use prompt with citations."""
    sources = "\n\n".join(
        f"[source: {c.source}]\n{c.text}" for c in contexts
    )
    return (
        "You are a defensive security assistant. Answer ONLY using the provided "
        "context. If the context is insufficient, say so. Cite sources by name. "
        "Do not provide instructions that enable attacking systems.\n\n"
        f"# Context\n{sources}\n\n# Question\n{question}\n\n# Answer"
    )


def ollama_generate(prompt: str) -> str:
    """Call the LOCAL Ollama endpoint. Imported lazily so the module loads even
    without httpx installed (e.g. during static analysis/tests)."""
    import httpx

    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    model = os.environ.get("OLLAMA_MODEL", "llama3.1")
    resp = httpx.post(
        f"{host}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=120.0,
    )
    resp.raise_for_status()
    return resp.json().get("response", "")
