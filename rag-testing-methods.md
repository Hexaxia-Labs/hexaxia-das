# DAS RAG Testing Methods

**Date:** 2026-05-28  
**Author:** Aaron Lamb  
**Status:** Complete — findings incorporated into spec v0.3 and nav-test-findings-260528.md

This document describes exactly how RAG-assisted navigation was tested against DAS corpora: what infrastructure was used, how documents were chunked and embedded, how queries were run, and what the results showed.

---

## Purpose

The nav-test benchmark measured whether a RAG pre-query could reduce agent navigation cost compared to blind filesystem traversal. The hypothesis: embed passport summaries, query at task time to get a DAS address, resolve that address to a folder path, and inject it as a routing hint before the agent begins navigating. If the routing hint is correct, the agent skips the early exploration turns and goes straight to the right area.

---

## Infrastructure

### Vector Store

**ChromaDB** — persistent client, local disk.

```
Path: ~/Projects/sage/.claude/rag/chroma_db
Collections: das_nav_test_nomic, das_nav_test_mxbai
```

ChromaDB runs in-process (no server). The same ChromaDB instance used by Sage's main RAG system, but in isolated test collections that do not overlap with `company_context` or `sage_episodes`.

### Embedding Models

**Ollama** — local, Windows native, port 11434. Two models tested:

| Key | Model | Context window | Chunk size used |
|---|---|---|---|
| `nomic` | `nomic-embed-text` | 8,192 tokens | 400 words |
| `mxbai` | `mxbai-embed-large` | 512 tokens | 200 words |

Called via HTTP:

```python
requests.post(
    "http://localhost:11434/api/embeddings",
    json={"model": "mxbai-embed-large", "prompt": text}
).json()["embedding"]
```

mxbai has a hard 512-token limit. The script truncates to 1800 / 1200 / 800 characters and retries on overflow.

### No External Services

No Synapaxia, no RhizomeRAG, no API calls outside localhost. The test stack is:

```
nav-test.py  →  rag_lookup()  →  Ollama (embed query)
                              →  ChromaDB (query passport chunks)
                              →  return das_address + folder_path
```

---

## Corpus

**Source:** `~/Projects/Hexaxia-Technologies-DAS/`

DAS test corpus: same content as the live `Hexaxia-Technologies` corpus, renamed to `{address}-HXT-{client}-{descriptor}-{YYMMDD}.md` format (the format before DAS v3 adoption), with passport blocks and `das.manifest.yaml` added.

**Skipped during embedding:**
- Files: `AGENT_CONTEXT.md`, `CLAUDE.md`, `README.md`, `GOOGLE-DRIVE-SYNC.md`, `das.manifest.yaml`, `das.config.yaml`
- Directories: `.git`, `.claude`, `.hextant`, `_drafts`
- Any path component starting with `_`

---

## Chunking Strategy

Each `.md` file produces two types of chunks:

### 1. Passport Chunk (dedicated, one per file)

Files with a Document Passport block get a single high-signal chunk formatted as:

```
[passport] {title} | type:{type} status:{status} address:{das_address}
{summary}
```

Example:

```
[passport] HXT-ULS-007 - NetBird ZTNA Deployment | type:runbook status:active address:02.01.04
Six-phase runbook to deploy NetBird ZTNA for United Life Services (ULS)...
```

Metadata stored with the chunk:
```python
{
    "source": "02.01.04-HXT-ULS-netbird-ztna-deployment-260509.md",
    "path": "02-Clients/02.01-ULS/02.01.04-Projects/02.01.04-HXT...",
    "das_address": "02.01.04",
    "chunk_type": "passport"
}
```

### 2. Content Chunks (sliding window)

Document body (passport block stripped) split into overlapping word windows:

| Model | Chunk size | Overlap |
|---|---|---|
| nomic | 400 words | 50 words |
| mxbai | 200 words | 50 words |

Content chunks carry `chunk_type: "content"` in metadata.

---

## Query Flow — `rag-nav` Variant

At test time, for each question:

1. **Embed the query** using the active Ollama model.
2. **Search passport chunks only** — `where={"chunk_type": "passport"}`, top 5 results by L2 distance.
3. **Take the best hit** (lowest distance). Extract `das_address` from its metadata.
4. **Resolve the address to a folder path** — scan the corpus directory for a folder whose name starts with `{das_address}-`.
5. **Inject as a navigation hint** — prepend to the question:
   ```
   RAG suggests starting at: 02-Clients/02.01-ULS/02.01.04-Projects/

   What blockers currently exist on the NetBird ZTNA deployment for ULS?
   ```
6. **Agent navigates from the hint** — if the hint is correct, the agent goes straight there. If wrong, it falls back to `ls .` from root.

The agent system prompt for `rag-nav` variants:

> "A RAG pre-search has provided a suggested starting folder path at the top of your task. Step 1: ls the suggested path first. If the contents don't match the question, ls the parent folder or navigate from root. Step 2: Read only relevant files. Step 3: Answer from file content only."

---

## Scripts

| Script | Location | Purpose |
|---|---|---|
| `rag-test.py` | `~/Projects/das-nav-test/rag-test.py` | Embed corpus, test retrieval accuracy |
| `nav-test.py` | `~/Projects/das-nav-test/nav-test.py` | Full nav benchmark — calls `rag_lookup()` inline |

### rag-test.py usage

```bash
# Embed corpus into ChromaDB (run once per model)
python3 rag-test.py --embed --model nomic
python3 rag-test.py --embed --model mxbai

# Test retrieval accuracy (passport hit rate against 8 questions)
python3 rag-test.py --query --model mxbai

# Wipe and re-embed
python3 rag-test.py --clean --embed --query --model mxbai
```

### nav-test.py — rag-nav variants

```bash
# Run rag-nav variants (uses mxbai by default via RAG_MODEL env var)
RAG_MODEL=mxbai python3 nav-test.py --corpus rag-nav

# nomic variant
RAG_MODEL=nomic python3 nav-test.py --corpus rag-nav
```

The `rag-nav-mxbai` and `rag-nav` (nomic) result columns in `RESULTS.md` are disambiguated by the `rag_model` field stored in each run JSON.

---

## Results

### Retrieval Accuracy (passport hit rate, 8 questions)

| Model | Correct address routing | Score |
|---|---|---|
| `nomic-embed-text` | 3 / 8 | 37.5% |
| `mxbai-embed-large` | 7 / 8 | **87.5%** |

The one miss for mxbai: Q4 ("list all active ULS projects") routes to the LinkedIn Scheduled folder instead of ULS Projects — "active projects" language overlaps with social post metadata. Fix: improve ULS project passport summaries to explicitly state project count and enumerate project names.

### Navigation Impact (turns, 8 questions, 3 runs each)

| Variant | Total turns | vs original |
|---|---|---|
| `rag-nav` (nomic) | 57.8 | -25% |
| `rag-nav-mxbai` | **51.7** | **-33%** |
| original (baseline) | 76.7 | — |
| das-manifest | 66.5 | -13% |

rag-nav-mxbai is the best-performing variant across all 11 tested. It also uses the fewest output tokens (13,736 vs 18,720 original).

### Q2 Exception

Q2 ("list all scheduled LinkedIn posts") is the one question where `das-manifest` beats `rag-nav-mxbai` (3.0 vs 4.3 turns). RAG misroutes to `04.05-Social` instead of `04.05.02.03-Scheduled` because the question doesn't use enough LinkedIn-specific language to distinguish the scheduled subfolder. The manifest reads the full address map and routes directly. For sub-tree enumeration questions, manifest-first remains the better pattern.

---

## Key Findings

1. **Embedding model selection is the highest-leverage RAG variable.** The swap from nomic → mxbai alone accounts for 6 fewer turns per run (57.8 → 51.7). Everything else — chunking, formatting, query construction — matters less than the model.

2. **Passport summary quality is the critical content variable.** RAG was queried exclusively on passport chunks. The `summary` field drives address routing accuracy. A well-written summary names the subject, type, key entities, and any facts an agent would query against. A generic or missing summary degrades mxbai toward nomic-level accuracy.

3. **Content chunks were embedded but not used in nav-test queries.** Only `chunk_type: "passport"` chunks were queried. Content chunks exist in the collection for potential future retrieval use but did not improve routing accuracy when mixed in — the passport chunk signal is cleaner.

4. **The pattern works without a manifest.** `rag-nav-mxbai` outperforms `das-manifest` overall even though the manifest is a complete corpus map. RAG is faster for direct lookup and cross-area questions; manifest wins for sub-tree enumeration. Default pattern: rag-nav-mxbai, fall back to manifest if RAG returns no result.

---

## Recommended Navigation Pattern for DAS Agents

```
1. Embed the user query (mxbai-embed-large via Ollama)
2. Query passport chunks: WHERE chunk_type = 'passport', top 5 by L2 distance
3. Take best hit → extract das_address
4. Resolve das_address → folder path (scan corpus root for matching folder name)
5. Inject: "RAG suggests starting at: {path}"
6. Agent navigates from hint, falls back to root ls if hint is wrong
7. If RAG returns no result: fall back to manifest-first (read das.manifest.yaml)
```

System prompt note: tell the agent the hint is a suggestion, not a guarantee. If the folder contents don't match the question, it should `ls` the parent or start from root.

---

## Passport Format (for embedding)

For RAG to work well on this corpus, every file should have a passport block:

```markdown
<!--
passport:
  title: "Document title"
  type: runbook          # controlled vocabulary — see spec §5.4
  status: active
  tags: [uls, netbird, ztna]
  das_address: "02.01.04"
  summary: "2-5 sentence description naming subject, type, key entities,
            and any facts an agent would query against. This field alone
            determines RAG routing accuracy."
-->
```

The `summary` field is the entire signal. Write it to answer the questions agents will ask, not to describe what the document is. "Contains the NetBird ZTNA deployment runbook for ULS, covering six phases, three current blockers..." will route correctly. "This document describes the deployment process..." will not.
