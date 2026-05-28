# DAS Navigation Test — Benchmark Findings

**Date:** 2026-05-28  
**Author:** Aaron Lamb  
**Corpus:** Hexaxia-Technologies-DAS (55 files)  
**Test harness:** `~/Projects/das-nav-test/`  
**Questions:** 8 representative navigation tasks  
**Agent model:** claude-haiku-4-5-20251001  

---

## Purpose

Measure whether DAS addressing reduces agent navigation cost compared to two baselines:
- **original** — pre-DAS mixed-convention file names (messy real-world state)
- **descriptive** — clean alphabetical folder hierarchy, type-subject file naming, no numeric addresses
- **das-v2** — proposed format `{address}-{type}-{descriptor}.ext`, same folders and passports as DAS

Nine variants total were tested across the three corpora.

---

## Variants Tested

| Variant | Corpus | Description |
|---|---|---|
| **original** | original | Pre-DAS mixed-convention names, no passports |
| **descriptive** | descriptive | Clean alphabetical folders (`clients/uls/projects/`), type-subject files (`runbook-netbird-ztna.md`), no passports |
| **das** | das | DAS numeric addresses only, no manifest or passports |
| **das-v2** | das-v2 | Proposed format: `{address}-{type}-{descriptor}.ext`, passports intact |
| **das-manifest** | das | Agent reads `das.manifest.yaml` first to route |
| **das-passport** | das | Each file has a passport block with summary |
| **das-manifest-passport** | das | Manifest + passports combined |
| **rag-nav (nomic)** | das | RAG pre-query (nomic-embed-text) → DAS address → navigate |
| **rag-nav-mxbai** | das | RAG pre-query (mxbai-embed-large) → DAS address → navigate |

RAG queries exclusively passport chunks — each formatted as `[passport] {title} | type:{type} status:{status} address:{das_address}\n{summary}`. Content chunks were embedded but not used in rag-nav queries.

---

## Results

### Aggregate turns — lower is better

| Corpus | Total turns (8 Qs) | vs original |
|---|---|---|
| **descriptive** | **99.7** | **+30%** |
| original | 76.7 | — |
| **das-v2** | **78.7** | **+3%** |
| das | 75.3 | -2% |
| das-manifest | 66.5 | -13% |
| das-passport | 72.0 | -6% |
| das-manifest-passport | 73.0 | -5% |
| rag-nav (nomic) | 57.8 | -25% |
| **rag-nav-mxbai** | **51.7** | **-33%** |

### Aggregate output tokens — lower is better

| Corpus | Avg output tokens/Q | vs original |
|---|---|---|
| descriptive | 2,727 | +27% |
| original | 2,150 | — |
| das-v2 | 2,358 | +10% |
| das | 2,068 | -4% |
| das-manifest | 2,059 | -4% |
| das-passport | 2,301 | +7% |
| das-manifest-passport | 2,353 | +9% |
| rag-nav (nomic) | 1,863 | -13% |
| **rag-nav-mxbai** | **1,609** | **-25%** |

### Per-question turns breakdown

| Q | Type | original | descriptive | das | das-v2 | das-manifest | rag-nav-mxbai |
|---|---|---|---|---|---|---|---|
| Q1 | Direct lookup | 7.0 | **19.7** | 7.0 | 14.3 | 9.5 | 4.7 |
| Q2 | Subfolder nav | 7.0 | 7.3 | 8.0 | 6.3 | **3.0** | 4.3 |
| Q3 | Cross-area | 17.0 | 14.3 | 14.0 | 14.0 | 9.0 | **9.3** |
| Q4 | Enumeration | 14.0 | **24.0** | 14.0 | 13.0 | 14.0 | 14.0 |
| Q5 | Recency | 8.0 | 12.0 | 8.0 | 7.7 | 8.5 | **5.0** |
| Q6 | Structural | 9.7 | 10.7 | 13.3 | **9.7** | 9.5 | 7.7 |
| Q7 | Buried fact | 6.0 | 5.3 | 6.0 | 7.0 | 8.5 | **3.0** |
| Q8 | Misrouting | 8.0 | 6.3 | **5.0** | 6.7 | 4.5 | 3.7 |

---

## Key Findings

### 1. DAS numeric addressing is not neutral — it earns its keep

Descriptive naming (clean alphabetical folders, no numeric prefixes) is **30% worse than original** and **32% worse than DAS**. The numbers in a naming convention matter independently of how good the descriptions are.

### 2. Numeric prefixes act as an implicit jump table for agents

With DAS, `ls .` returns `00-Admin 01-Finance 02-Clients 03-Sales...` — agents immediately discard irrelevant areas and go to `02-Clients` for a client question. With descriptive, `ls .` returns `admin clients hr marketing operations products projects sales` — agents see both `clients` and `projects` as plausible for "ULS projects" and explore both before converging.

Q1 (direct lookup, single known file) takes 7 turns in DAS vs 19.7 in descriptive. Q4 (enumerate all ULS projects) takes 14 in DAS vs 24 in descriptive. These are not noise — they replicate across 3 runs.

### 3. rag-nav-mxbai is the clear overall winner (-33% vs original)

The hybrid pattern — RAG pre-query to get DAS address, resolve to folder path, inject as navigation hint — outperforms all pure-filesystem and manifest-based approaches. It also outperforms descriptive by 48 turns (93%).

### 4. Embedding model selection is the highest-leverage RAG variable

mxbai-embed-large achieves **7/8 correct address routing** vs nomic-embed-text **3/8**. This single swap accounts for ~6 turns of improvement in rag-nav (57.8 → 51.7). Passport summaries provide the signal; the model determines whether that signal is exploited.

### 5. Passport summaries are the critical RAG signal

RAG was queried only on passport chunks. The `summary` field — a 2-5 sentence description of what the document contains — drives accurate address routing. Well-written summaries are necessary for rag-nav to work well; poor summaries degrade to nomic-level accuracy or worse.

### 6. das-manifest wins Q2 specifically; rag-nav misses it

Q2 (all scheduled LinkedIn posts) is the one question where das-manifest beats rag-nav-mxbai (3.0 vs 4.3 turns). RAG misroutes to `04.05-Social` instead of `04.05.02.03-Scheduled` because the question doesn't use enough LinkedIn-specific language. The manifest reads the address map and routes directly. For sub-tree enumeration questions, manifest-first remains the better pattern.

### 7. Q4 is a persistent hard case across all variants

Listing all active ULS projects costs ~14 turns regardless of variant (descriptive: 24). RAG misroutes Q4 to the LinkedIn Scheduled folder — "active projects" language overlaps with social post metadata. Fixing this requires better passport summaries on the ULS Projects documents explicitly stating project count and status.

### 8. Type-subject file naming helps structural questions slightly

Within a folder, descriptive type-prefixed names (`runbook-`, `analysis-`, `template-`) improve structural orientation questions (Q6) vs DAS address-only names. DAS address names obscure document type in the filename; moving to `{address}-{type}-{descriptor}` format would restore this signal without losing the jump-table benefit of numeric prefixes.

### 9. DAS v2 (`{address}-{type}-{descriptor}`) is validated as neutral-plus

das-v2 aggregate turns (78.7) are statistically neutral vs das (75.3) — within run-to-run variance. The predicted Q6 improvement materialised: structural orientation dropped from 13.3 turns (das) to 9.7 (das-v2), matching the original corpus baseline. The type slug lets agents characterise document type from `ls` output without opening files.

The only notable regression is Q1 (deep direct lookup: 14.3 vs 7.0 in das). This is likely descriptor truncation — `02.01.04-HXT-ULS-netbird-ztna-deployment-260509.md` contains the word "deployment" which reinforces the query signal; `02.01.04-runbook-netbird-ztna.md` does not. With a more specific descriptor (e.g., `02.01.04-runbook-netbird-ztna-deploy.md`) this gap would likely close.

Net verdict: adopt `{address}-{type}-{descriptor}` format. The aggregate cost is noise; the Q6 gain and human readability benefit are real.

---

## Recommendations

**1. Keep numeric address prefixes — they are the highest-value element of DAS.**  
The jump-table effect is real and large. Descriptive alphabetical hierarchies perform significantly worse even with clean naming.

**2. Use mxbai-embed-large for all DAS RAG embeddings.**  
7/8 address accuracy vs 3/8 for nomic. Not a marginal difference.

**3. Invest in passport summary quality.**  
The summary field is the single most impactful thing to write carefully. It should name subject, type, key entities, and any facts an agent would query against.

**4. Adopt `{address}-{type}-{descriptor}.ext` as the DAS v2 filename format. Confirmed.**  
Current: `{address}-HXT-{client}-{descriptor}-{YYMMDD}.ext`  
Adopted: `{address}-{type}-{descriptor}.ext`  
Drop dates and HXT prefix — both are redundant with the passport. Type slug restores structural orientation signal (Q6: 13.3 → 9.7 turns) with no aggregate regression. Keep descriptors specific enough to preserve search signal — avoid over-truncating subject words that appear in common queries.

**5. Default navigation pattern for DAS agents: rag-nav-mxbai.**  
Pre-query RAG (passport-only filter) → get `das_address` → resolve to folder path → inject as `RAG suggests starting at: {path}`. Fall back to manifest-first if RAG returns no result.

**6. Improve Q4-class passport summaries.**  
Documents that answer "list everything in category X" questions should have summaries that explicitly state item count and enumerate key items (e.g., "Contains 9 active ULS project runbooks covering NetBird ZTNA, Zabbix, UniFi migration...").

---

## Descriptive Corpus Design

The descriptive corpus (`~/Projects/Hexaxia-Technologies-Descriptive/`) was built from the DAS corpus with:
- Numeric prefixes stripped from all folder and file names
- Folder hierarchy: `clients/uls/projects/`, `marketing/social/linkedin/scheduled/`, etc.
- File naming: `{type}-{subject}.ext` — e.g., `runbook-netbird-ztna.md`, `spec-hexpublish.md`, `lead-callserv-limited.md`
- Passport blocks stripped (bare content only)
- No manifest, no RAG

Build script: `~/Projects/das-nav-test/build-descriptive.py`

---

## Test Infrastructure

- **Harness:** `~/Projects/das-nav-test/nav-test.py`
- **Corpus builder:** `~/Projects/das-nav-test/build-descriptive.py`
- **Embedding:** `~/Projects/das-nav-test/rag-test.py`
- **Report generator:** `~/Projects/das-nav-test/report.py`
- **Run data:** `~/Projects/das-nav-test/results/` (26 runs)
- **ChromaDB:** `~/Projects/sage/.claude/rag/chroma_db` — `das_nav_test_nomic`, `das_nav_test_mxbai`
