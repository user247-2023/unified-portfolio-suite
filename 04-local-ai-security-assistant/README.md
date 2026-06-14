# Local AI Security Assistant

A privacy-preserving security assistant that runs entirely on local
infrastructure. It answers security questions and triages alerts using a local
LLM (via Ollama) grounded in your own documentation through retrieval-augmented
generation (RAG) — no data leaves the machine.

## Problem

Security teams want LLM assistance (explaining a CVE, summarizing an alert,
drafting a runbook) but can't paste logs, configs, or vulnerability details into
a third-party API. Sending sensitive security context to an external SaaS is
often a policy or compliance violation.

## Solution

- **Local-only inference** with [Ollama](https://ollama.com) — the model runs on
  your hardware; prompts and documents never leave the host.
- **RAG over your corpus.** Security docs (runbooks, policies, past incidents)
  are chunked, embedded, and stored in a local FAISS index. Answers are grounded
  in retrieved context and cite their sources.
- **Guardrails.** A system prompt constrains the assistant to defensive,
  advisory use; retrieval keeps it grounded rather than hallucinating.

## Tech Stack

- **Python 3.12**
- **Ollama** — local model serving (e.g. `llama3.1`, `qwen2.5`).
- **FAISS** — fast local vector similarity search.
- **sentence-transformers** — local embeddings (no external embedding API).

## Usage

```bash
# 1) Install and start Ollama, then pull a model:
ollama pull llama3.1

pip install -r requirements.txt

# 2) Index your security docs (local folder):
python -m assistant index ./my-security-docs

# 3) Ask grounded questions (uses the local model):
python -m assistant ask "How do we respond to a suspected phishing report?" --docs ./my-security-docs

# Retrieval-only (no model needed) — see which docs ground the answer:
python -m assistant ask "phishing report" --docs ./my-security-docs --no-model

# Run the offline RAG test suite (pure stdlib — no faiss/ollama needed):
python -m unittest discover -s tests -v
```

The retrieval core ships a dependency-free path: a deterministic hashing
embedder + cosine-similarity `VectorStore` (`assistant/rag/store.py`) so
retrieval runs and is tested without faiss or a running model. Swapping in
`sentence-transformers` later changes one class — the `Retriever` interface is
identical.

Configuration (model name, Ollama host) is read from environment variables; see
`.env.example`.

## Security Considerations

- **Data locality.** Inference and embeddings are 100% local; the assistant
  makes no outbound network calls except to the local Ollama endpoint.
- **No secrets in prompts.** The indexer skips files matching secret patterns
  (`.env`, `*.key`) so credentials are never embedded into the vector store.
- **Grounded, cited answers.** Responses include the source chunks used,
  reducing hallucination risk and making advice auditable.
- **Advisory only.** The assistant is scoped to explanation and triage support;
  it does not execute actions against systems.

## Lessons Learned

- RAG mattered more than model size: a small local model with good retrieval beat
  a bigger model answering from memory.
- Excluding secret-bearing files at index time is essential — otherwise a vector
  store quietly becomes a secrets store.
- Returning citations turned the tool from "a chatbot" into "something a SOC
  analyst will actually trust."
