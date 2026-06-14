"""CLI for the Local AI Security Assistant.

Purpose: `index <dir>` builds a local FAISS index from your docs; `ask <q>`
retrieves context and queries the local model. Kept thin; logic lives in
`assistant.rag.pipeline`.

Security note: nothing here makes an outbound call except to the local Ollama
host. The indexer excludes secret-bearing files (see pipeline.discover_documents).
"""
from __future__ import annotations

import click

from .rag.pipeline import (
    build_prompt,
    chunk_text,
    discover_documents,
    ollama_generate,
)


@click.group()
def cli() -> None:
    """Privacy-preserving, local-only security assistant."""


@cli.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False))
def index(directory: str) -> None:
    """Chunk and (in a full build) embed documents under DIRECTORY."""
    docs = discover_documents(directory)
    total_chunks = 0
    for path in docs:
        text = path.read_text(encoding="utf-8", errors="ignore")
        total_chunks += len(chunk_text(text, source=str(path)))
    click.echo(f"Indexed {len(docs)} document(s) into {total_chunks} chunk(s).")
    click.echo("Embeddings + FAISS persistence run in the full pipeline build.")


@cli.command()
@click.argument("question")
def ask(question: str) -> None:
    """Answer QUESTION grounded in retrieved local context."""
    # In the full pipeline this retrieves top-k chunks from FAISS; the prompt
    # builder + local model call below are the real, runnable path.
    contexts: list = []  # populated by retrieval in the full build
    prompt = build_prompt(question, contexts)
    try:
        click.echo(ollama_generate(prompt))
    except Exception as exc:  # noqa: BLE001 - surface, don't swallow
        click.echo(f"Local model call failed ({exc}). Is Ollama running?", err=True)


if __name__ == "__main__":
    cli()
