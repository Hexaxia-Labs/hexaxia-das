# DAS Navigation Benchmark Design

**Date:** 2026-05-28  
**Author:** Aaron Lamb  
**Status:** Complete — this benchmark is a closed study; findings incorporated into spec v0.3  
**See also:** `nav-test-findings-260528.md`, `naming-convention-analysis-260528.md`, `../../rag-testing-methods.md`

This document covers the design rationale behind the DAS navigation benchmark: what questions were tested, what each was designed to measure, how to interpret results, and the known limitations of this study.

---

## Purpose

The benchmark answers two questions:

1. **Navigation efficiency:** How much does the DAS naming convention reduce the number of agent turns needed to answer document-retrieval questions, compared to descriptive or unstructured naming?
2. **Discovery efficiency:** Do filename tags and/or passport tags meaningfully reduce the turns needed to enumerate all documents for a given entity?

These are operational questions. The goal was not to evaluate general agent intelligence, but to measure the concrete cost difference of one naming convention versus another for real retrieval tasks.

---

## Question Taxonomy

### Navigation Questions (Q1-Q8)

Eight questions designed to exercise different retrieval patterns. Model: `claude-haiku-4-5-20251001`. Three runs per variant.

| Q | Description | What it tests |
|---|---|---|
| Q1 | NetBird ZTNA deployment blockers for ULS | Deep direct lookup — requires navigating to a specific file. Tests whether the address jump-table helps agents discard irrelevant areas fast. |
| Q2 | List all scheduled LinkedIn posts | Sub-tree enumeration — requires finding `04.05.02.03-Scheduled/`. Tests whether RAG or manifest can route to a specific sub-folder vs blind traversal. |
| Q3 | What deliverables have been sent to Pax Nocturna in the last 60 days? | Cross-area lookup — deliverables may live in multiple client or project folders. Tests whether address prefix reduces cross-area scan cost. |
| Q4 | List all active ULS projects | Client-scoped enumeration within a specific area. Tests whether tags or passport metadata can narrow scope from ls output without opening files. |
| Q5 | What is the current NetBird pricing tier? | Product/reference lookup — a specific fact buried in a reference doc. Tests whether filename type slugs help agents skip non-reference files. |
| Q6 | What types of documents exist in the 03-Business area? | Structural orientation — requires reading folder/file structure and characterizing by type. Tests whether type slug in filenames reduces file-open cost. |
| Q7 | What proposal was sent to Shine Distributors? | Entity-name lookup across a leads/proposals area. Tests discriminability of descriptor tokens in filenames. |
| Q8 | Find the most recent Pax Nocturna strategy document | Multi-step: find client area, find strategy type, verify recency. Tests combined address + type slug signal under ambiguous naming. |

**What counts as a turn:** Each `ls`, `Read`, `find`, `grep`, or other tool call by the agent counts as one turn. The final answer message does not count. Lower is better.

### Discovery Questions (D1-D4)

Four questions designed specifically to test corpus-wide entity enumeration. Model: `claude-haiku-4-5-20251001`. Three passes per variant.

| Q | Description | What it tests |
|---|---|---|
| D1 | List all documents related to United Life Services | High-volume tag lookup (10 ULS-tagged files). Tests whether filename search is faster than blind navigation across the entire corpus. |
| D2 | List all documents related to Pax Nocturna | Lower-volume tag lookup (4 PN-tagged files). Tests whether tag-pp (passport grep) can match tag-fn when the search string (`pax-nocturna`) is distinctive. |
| D3 | List all sales leads for Trinidad | Specific sub-category enumeration (3 TT-tagged leads). Tests whether `find . -name '*-TT-*'` or passport grep is more reliable than blind navigation. |
| D4 | List all client-facing documents across all clients | Cross-client sweep — no single tag answers it. Tests whether agents can generalize the tag strategy across multiple codes. |

**Variants tested:**

| Variant | Strategy | Corpus | Allowed tools |
|---|---|---|---|
| `tag-fn-blind` | Blind `ls` traversal (baseline) | real-v3 | `ls`, `Read` |
| `tag-fn` | `find . -name '*-TAG-*' -type f` | real-v3 | `ls`, `Read`, `find *` |
| `tag-pp` | `grep -rl 'TAG' .` on passport blocks | das-v2 + passports | `ls`, `Read`, `grep *` |

D1-D4 are only run on discovery variants, not on navigation variants.

---

## Corpus Variants

All 14 tested variants, each defined by a `(corpus_path, system_prompt, allowed_tools)` tuple in `nav-test.py`:

| Variant | Corpus | Description |
|---|---|---|
| `original` | Hexaxia-Technologies raw | Pre-DAS mixed convention, baseline |
| `das` | DAS test corpus | `{address}-HXT-{client}-{descriptor}-{YYMMDD}` format |
| `das-v2` | DAS v2 test corpus | `{address}-{type}-{descriptor}` (no tag, no dates, no org) |
| `das-v3` | DAS v3 test corpus | `{address}-[{TAG}-]{type}-{descriptor}` (selective tags on client docs) |
| `real-v3` | Live Hexaxia-Technologies corpus | DAS v3 filenames, plain folder names, no passports, no manifest |
| `descriptive` | Descriptive corpus | No numeric prefixes, alphabetical type-subject names |
| `das-manifest` | DAS corpus + manifest read | Variant with `das.manifest.yaml` pre-injected into system prompt |
| `das-passport` | DAS corpus + passports | Variant with passport blocks searchable |
| `das-manifest-passport` | DAS corpus + both | Both manifest and passport context pre-loaded |
| `rag-nav` | DAS corpus + RAG hint (nomic) | Pre-query with nomic-embed-text → address → folder path hint |
| `rag-nav-mxbai` | DAS corpus + RAG hint (mxbai) | Pre-query with mxbai-embed-large → address → folder path hint |
| `tag-fn-blind` | real-v3 | Blind navigation baseline for discovery questions |
| `tag-fn` | real-v3 | Filename tag search (`find . -name '*-TAG-*'`) |
| `tag-pp` | DAS v2 + passports | Passport tag grep (`grep -rl 'TAG'`) |

---

## Interpreting Results

### Variance Thresholds

Each variant runs 3 passes per question. A 3-run average is noisy — treat results as directional, not precise.

**Rule of thumb:**
- Difference < 1.5 turns per question: within noise, do not treat as signal
- Difference 1.5-3.0 turns per question: directional signal, confirms hypothesis
- Difference > 3.0 turns per question: strong signal, use in spec decisions

**Aggregate vs. per-question:** Aggregate (sum across all questions) reduces noise but masks question-type effects. Always check per-question breakdown before citing aggregate numbers. A variant may win overall but lose on specific question types (e.g., `das-manifest` beats `rag-nav-mxbai` on Q2).

**Regression watchlist:** Any change that saves turns on some questions but costs turns on others needs per-question analysis. Tags are the clearest example: +4 turns on Q1/Q3, -2 turns on Q4/Q8. Aggregate looked negative; the decomposition explains why.

### Known Limitations

**Small corpus.** 56 files in the real-v3 corpus; ~30-40 addressable files in test corpora. A larger corpus with more deep nesting would amplify or reverse some effects. Address prefix benefit may be higher; tag parsing cost may be higher.

**Fixed questions.** Q1-Q8 and D1-D4 were written to cover different question types but are not statistically representative of a real agent workload. The rankings reflect this specific question set.

**Single agent model.** All runs used `claude-haiku-4-5-20251001`. A larger model may navigate more efficiently in the blind variants, compressing the benefit of structure. A smaller/faster model may show larger gains.

**3 runs per variant.** Too few for statistical significance. Some question-level variance is noise. Use 5+ runs for any variant before citing it in a spec decision.

**Controlled corpus.** The test corpus was purpose-built to match DAS conventions. A real-world corpus with mixed adoption would have noisier results.

**Turn count as proxy.** Turns measure tool invocations, not wall-clock time or cost. A `find` that returns immediately counts the same as a `Read` on a large file. Token cost and latency are not measured here.

### What the Q-labels mean

- **Qn** questions are navigation questions (Q1-Q8) — single-answer, specific retrieval
- **Dn** questions are discovery questions (D1-D4) — enumeration across corpus, no single answer

These are separate test sets run on separate variant groups.

---

## Adding a New Corpus Variant

To test a new variant, edit `~/Projects/das-nav-test/nav-test.py`:

1. **Define the corpus path.** Either use an existing corpus constant or define a new one. The corpus must be a local directory with the naming convention you want to test.

2. **Write or select a system prompt.** The system prompt tells the agent what convention is in use and how to navigate. Minimal prompt = blind navigation. Descriptive prompt = convention-aware.

3. **Define allowed tools.** Pass `None` to use Typer's default Claude Code tool restrictions (ls + Read). Pass a space-separated string like `"Bash(ls *) Bash(find *) Read"` to extend.

4. **Add the entry to CORPORA:**
   ```python
   CORPORA = {
       ...
       "my-variant": (CORPUS_MY_PATH, SYSTEM_PROMPT_MY_VARIANT, MY_TOOLS),
   }
   ```

5. **Run:** `python3 nav-test.py --corpus my-variant`

6. **Add to report.py** if you want it included in RESULTS.md:
   - Add to `CORPUS_ORDER` list
   - Add any new questions to `QUESTION_LABELS`

7. **Run `report.py`** to regenerate RESULTS.md.

---

## Open Questions

These questions were not tested in this study and remain open for future work:

**1. Larger corpora.** Does the address jump-table benefit scale with corpus size? At 200 files or 2,000 files, the address becomes more important as the search space grows. Expected: benefit increases with depth, not just width.

**2. Mixed adoption.** What happens with a corpus that is 50% DAS-named and 50% legacy? Does partial adoption help or hurt? Does the agent get confused by mixed signals?

**3. Passport + RAG for discovery.** `rag-nav-mxbai` was only tested on Q1-Q8. Could a RAG pre-query on passport summaries replace filename tag search for D1-D4? Expected: RAG wins on Q1-class direct lookup; tag-fn wins on D1-class enumeration (because `find` returns all matching files, while RAG returns the top-1 hit).

**4. Better passport summaries.** The one mxbai miss (Q4) was traced to a weak passport summary for the ULS projects folder. No variant with improved summaries was tested. Expected: correcting the ULS projects passport summary fixes Q4 routing and brings mxbai to 8/8.

**5. Manifest + RAG hybrid.** `das-manifest` wins Q2 (sub-tree enumeration) where `rag-nav-mxbai` loses. A hybrid that tries RAG first and falls back to manifest was proposed but not tested.

**6. Longer runs.** 3 passes per variant at 8 questions = 24 data points. At 5 passes, confidence intervals improve substantially. A 5-run rerun of `rag-nav-mxbai` vs `original` with the improved passport summary would sharpen the finding.

**7. Cost measurement.** Token cost per question was not captured in the test harness (only turn count). For production decisions, cost-per-correct-answer is the better metric — rag-nav-mxbai may have a different cost profile than the turn count suggests if the RAG embed step has overhead.

---

## Relationship to Spec

The benchmark findings fed directly into `docs/spec.md` v0.3:

| Finding | Spec change |
|---|---|
| Address prefix -30% regression without it | §5.1 — address required |
| Type slug confirmed (Q6 -27%) | §5.4 — type required, 15-type hard cap |
| Folder address prefix redundant (real-v3 = 77.7 vs 75.3 das) | §4.2 — folder prefix not required |
| Tag costs nav (-4 Q1, -3 Q3), helps enumeration (-2 Q4, -1.4 Q8) | §5.3 Rule 6 — apply selectively |
| Filename tag find: -56% on D1-D4 | §10.1 — discovery primitive |
| Passport grep unreliable for common strings | §5.3 Rule 6 note |
| mxbai 7/8 routing, nomic 3/8 | `rag-testing-methods.md` |
| Passport summary quality = primary RAG variable | `docs/writing-passport-summaries.md` |

---

## Result Files

All 38 run JSONs are in `~/Projects/das-nav-test/results/`. Each file: `{variant}-{YYYYMMDD}-{HHMMSSmmm}.json`. Fields: `corpus`, `variant`, `question_id`, `question`, `turns`, `answer`, `run_date`, `rag_model` (for rag-nav variants only).

`RESULTS.md` is generated by `report.py` from these files. It is authoritative for published numbers.
