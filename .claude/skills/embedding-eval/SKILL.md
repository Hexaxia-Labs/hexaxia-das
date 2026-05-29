---
name: embedding-eval
description: Use when an ML or retrieval change needs empirical validation against the DAS nav-test benchmark harness. Documents the external harness, how to add a variant, and how to read results. Triggers on "benchmark this", "does this embedding help", "measure navigation cost", "run nav-test", "validate the retrieval change".
---

# embedding-eval

Validate a retrieval/ML change empirically against the navigation benchmark before citing it
in the spec. The harness is a **separate local project, not in this repo**, and not on
GitHub. The committed research docs in `docs/research/` are its output.

## Harness location and scripts

`~/Projects/das-nav-test/`
- `nav-test.py` - main runner; calls `rag_lookup()` inline for rag-nav variants.
- `rag-test.py` - embed corpus + test retrieval accuracy (passport hit rate).
- `report.py` - regenerates `RESULTS.md` from run JSONs in `results/`.

Infrastructure: ChromaDB at `~/Projects/sage/.claude/rag/chroma_db` (collections
`das_nav_test_nomic`, `das_nav_test_mxbai`); Ollama on port 11434 (`mxbai-embed-large`,
`nomic-embed-text`). Read `rag-testing-methods.md` in this repo for the full pipeline.

## Running

```bash
cd ~/Projects/das-nav-test
# embed (once per model)
python3 rag-test.py --embed --model mxbai
# retrieval accuracy
python3 rag-test.py --query --model mxbai
# full nav benchmark for a variant
RAG_MODEL=mxbai python3 nav-test.py --corpus rag-nav-mxbai
# regenerate the report
python3 report.py
```

## Adding a variant

Edit `nav-test.py`: add a `(corpus_path, system_prompt, allowed_tools)` entry to `CORPORA`,
run `python3 nav-test.py --corpus <name>`, then add it to `report.py` (`CORPUS_ORDER`,
`QUESTION_LABELS`) and regenerate. Full steps in `benchmark-design-260528.md`.

## Reading results (variance thresholds)

3 runs per variant is noisy - treat as directional.
- < 1.5 turns/question difference: noise, not signal.
- 1.5-3.0 turns/question: directional, confirms a hypothesis.
- > 3.0 turns/question: strong signal, usable in spec decisions.
Always check the per-question breakdown before citing an aggregate. **Use 5+ runs before any
spec decision.** Turn count is a proxy - it does not measure token cost or latency.

Recall/store outcomes via `synapaxia-memory`. Hand validated findings back to
`retrieval-design` / `das-feature-tdd`.
