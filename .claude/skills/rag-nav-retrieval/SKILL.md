---
name: rag-nav-retrieval
description: Use when retrieving or answering a question from a DAS corpus - finding which document holds an answer, or navigating to the right address. Implements the validated rag-nav pattern with graceful fallbacks. Triggers on "find the doc about", "where is", "what does the corpus say about", "look up in the corpus", or any content question against an addressed corpus.
---

# rag-nav-retrieval

The validated navigation pattern for DAS corpora (benchmark: rag-nav-mxbai is -33% turns
vs blind). Use the strongest path available, degrade gracefully, and always answer from
file content - never from the passport summary alone.

## Path A - RAG pre-query (best, when available)

Available only if Ollama (port 11434) is up AND the corpus has been embedded into a
ChromaDB passport collection. See `rag-testing-methods.md` for the embed pipeline.

1. Embed the user query with `mxbai-embed-large` via Ollama
   (`POST http://localhost:11434/api/embeddings`). mxbai routes 7/8 vs nomic 3/8 - use mxbai.
2. Query passport chunks only: `where={"chunk_type": "passport"}`, top 5 by L2 distance.
3. Take the best hit, extract `das_address` from its metadata.
4. Resolve the address to a folder path (scan corpus root for a folder name starting with
   `{das_address}-`, or read the manifest).
5. Treat it as a hint: `ls` that path first. If contents don't match the question, `ls` the
   parent or start from root.

## Path B - manifest-first (fallback, and preferred for sub-tree enumeration)

Use when RAG is unavailable, returns nothing, or the question is a sub-tree enumeration
(Q2-class, e.g. "list all scheduled LinkedIn posts") - manifest beats RAG there (Q2 misroute).

1. Read `das.manifest.yaml`. It is the full address map.
2. Match the question to a label/description; route directly to that address's folder.
3. `.venv/bin/das find <term>` and `.venv/bin/das ls <address>` help narrow.

## Path C - filesystem jump-table (always available)

Use when there is no manifest and no RAG.

1. `ls .` at corpus root. Numeric prefixes (`00-Admin 01-Finance 02-Clients ...`) are a
   jump-table - discard irrelevant areas immediately and descend the relevant one.
2. The `{type}` slug in filenames tells you document intent without opening
   (`...-runbook-...`, `...-report-...`). Read only relevant files.

## Discovery (enumerate all docs for an entity)

When asked to list every document for a client/category, prefer filename tag search:
`find . -name '*-TAG-*' -type f` (benchmark: -56% vs blind). Passport grep
(`grep -rl 'tag' .`) works only when the tag string is distinctive.

## Always

- Answer from the content of files you actually Read, not from passport summaries.
- Before starting, recall via the `synapaxia-memory` skill; after, store what worked
  (e.g. which path won for this question class on this corpus).
