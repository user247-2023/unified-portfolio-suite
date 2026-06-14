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
from .rag.store import Retriever


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


def _build_retriever(directory: str) -> Retriever:
    """Index a docs directory with the offline retriever (no model needed)."""
    retriever = Retriever()
    for path in discover_documents(directory):
        text = path.read_text(encoding="utf-8", errors="ignore")
        retriever.index(chunk_text(text, source=str(path)))
    return retriever


@cli.command()
@click.argument("question")
@click.option("--docs", type=click.Path(exists=True, file_okay=False),
              help="Directory of docs to ground the answer in.")
@click.option("-k", "top_k", default=3, show_default=True,
              help="Number of context chunks to retrieve.")
@click.option("--no-model", is_flag=True,
              help="Retrieve + show context only; skip the local model call.")
def ask(question: str, docs: str | None, top_k: int, no_model: bool) -> None:
    """Answer QUESTION grounded in retrieved local context."""
    contexts = _build_retriever(docs).retrieve(question, top_k) if docs else []

    if contexts:
        click.echo("Retrieved context:")
        for c in contexts:
            click.echo(f"  - {c.source}")

    if no_model:
        return

    prompt = build_prompt(question, contexts)
    try:
        click.echo(ollama_generate(prompt))
    except Exception as exc:  # noqa: BLE001 - surface, don't swallow
        click.echo(f"Local model call failed ({exc}). Is Ollama running?", err=True)


if __name__ == "__main__":
    cli()
