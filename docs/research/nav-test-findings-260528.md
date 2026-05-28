# DAS Navigation Test — Benchmark Findings

**Date:** 2026-05-28  
**Author:** Aaron Lamb  
**Corpus:** Hexaxia-Technologies-DAS (55 files)  
**Test harness:** `~/Projects/das-nav-test/`  
**Questions:** 8 navigation tasks (Q1-Q8) + 4 tag discovery tasks (D1-D4)  
**Agent model:** claude-haiku-4-5-20251001  

---

## Purpose

Measure whether DAS addressing reduces agent navigation cost compared to two baselines:
- **original** — pre-DAS mixed-convention file names (messy real-world state)
- **descriptive** — clean alphabetical folder hierarchy, type-subject file naming, no numeric addresses
- **das-v2** — `{address}-{type}-{descriptor}.ext`, same folders and passports as DAS
- **das-v3** — `{address}-[{TAG}-]{type}-{descriptor}.ext`, optional tag vocabulary applied selectively
- **real-v3** — DAS v3 filenames applied to the live `Hexaxia-Technologies` corpus, plain folder names (no address in folder names), no passports, no manifest

Eleven variants total were tested across four corpora.

---

## Variants Tested

| Variant | Corpus | Description |
|---|---|---|
| **original** | original | Pre-DAS mixed-convention names, no passports |
| **descriptive** | descriptive | Clean alphabetical folders (`clients/uls/projects/`), type-subject files (`runbook-netbird-ztna.md`), no passports |
| **das** | das | DAS numeric addresses only, no manifest or passports |
| **das-v2** | das-v2 | `{address}-{type}-{descriptor}.ext`, passports intact, no tags |
| **das-v3** | das-v3 | `{address}-[{TAG}-]{type}-{descriptor}.ext`, tags on client/market-scoped docs |
| **real-v3** | real | Live `Hexaxia-Technologies` corpus with DAS v3 filenames; plain folder names, no passports, no manifest |
| **das-manifest** | das | Agent reads `das.manifest.yaml` first to route |
| **das-passport** | das | Each file has a passport block with summary |
| **das-manifest-passport** | das | Manifest + passports combined |
| **rag-nav (nomic)** | das | RAG pre-query (nomic-embed-text) → DAS address → navigate |
| **rag-nav-mxbai** | das | RAG pre-query (mxbai-embed-large) → DAS address → navigate |
| **tag-fn-blind** | real | Blind navigation on real-v3 corpus — discovery baseline, no tag guidance |
| **tag-fn** | real | `find . -name '*-TAG-*'` filename tag search — agent uses tag codes in filenames |
| **tag-pp** | das-v2 | `grep -rl 'tag' .` passport tag search — agent reads passport `tags:` fields |

14 variants total. tag-fn/tag-pp ran against 4 discovery questions (D1-D4); all other variants ran against 8 navigation questions (Q1-Q8).

RAG queries exclusively passport chunks — each formatted as `[passport] {title} | type:{type} status:{status} address:{das_address}\n{summary}`. Content chunks were embedded but not used in rag-nav queries.

---

## Results

### Aggregate turns — lower is better

| Corpus | Total turns (8 Qs) | vs original |
|---|---|---|
| **descriptive** | **99.7** | **+30%** |
| das-v3 | 85.0 | +11% |
| original | 76.7 | — |
| **real-v3** | **77.7** | **+1%** |
| das-v2 | 78.7 | +3% |
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
| das-v3 | 2,598 | +21% |
| original | 2,150 | — |
| real-v3 | 2,337 | +9% |
| das-v2 | 2,358 | +10% |
| das | 2,068 | -4% |
| das-manifest | 2,059 | -4% |
| das-passport | 2,301 | +7% |
| das-manifest-passport | 2,353 | +9% |
| rag-nav (nomic) | 1,863 | -13% |
| **rag-nav-mxbai** | **1,609** | **-25%** |

### Per-question turns breakdown

| Q | Type | original | descriptive | das | das-v2 | das-v3 | real-v3 | das-manifest | rag-nav-mxbai |
|---|---|---|---|---|---|---|---|---|---|
| Q1 | Direct lookup | 7.0 | **19.7** | 7.0 | 14.3 | 18.3 | 11.3 | 9.5 | 4.7 |
| Q2 | Subfolder nav | 7.0 | 7.3 | 8.0 | 6.3 | 9.0 | 7.3 | **3.0** | 4.3 |
| Q3 | Cross-area | 17.0 | 14.3 | 14.0 | 14.0 | 16.7 | 13.7 | 9.0 | **9.3** |
| Q4 | Enumeration | 14.0 | **24.0** | 14.0 | 13.0 | **11.3** | 12.3 | 14.0 | 14.0 |
| Q5 | Recency | 8.0 | 12.0 | 8.0 | 7.7 | 8.3 | 8.7 | 8.5 | **5.0** |
| Q6 | Structural | 9.7 | 10.7 | 13.3 | **9.7** | **9.7** | 10.0 | 9.5 | 7.7 |
| Q7 | Buried fact | 6.0 | 5.3 | 6.0 | 7.0 | 6.3 | 6.0 | 8.5 | **3.0** |
| Q8 | Misrouting | 8.0 | 6.3 | **5.0** | 6.7 | 5.3 | 8.3 | 4.5 | 3.7 |

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

### 10. Tags add targeted value but carry in-corpus navigation cost

das-v3 aggregate (85.0 turns) is worse than das-v2 (78.7) and das (75.3). The tag adds tokens to every `ls` line — agents parsing `02.01.04-ULS-runbook-netbird-ztna-deploy.md` must process one more component before deciding relevance. This is visible in Q1 (18.3 vs 14.3 das-v2) and Q3 (16.7 vs 14.0), both broad navigation tasks where the agent scans many filenames.

However the tag delivers on its intended purpose in targeted queries:
- **Q4 enumeration** (list all active ULS projects): 11.3 vs 13.0 das-v2 — the `ULS` tag on project files lets the agent confirm client scope from `ls` without opening each file
- **Q6 structural orientation**: holds the das-v2 gain (9.7), no regression
- **Q8 misrouting trap**: 5.3 vs 6.7 das-v2 — tag helps agent skip irrelevant product folders

The trade-off is clear: tags help questions that need client/market disambiguation; tags hurt questions that require broad scanning. The tag is a human-readability and out-of-context feature first — the in-corpus navigation cost is real but modest at 3 files per question. For a human opening files from a search result or git log, the tag still earns its place.

### 11. DAS v3 filenames alone are sufficient — address in folder names is not required

real-v3 (live `Hexaxia-Technologies` corpus, DAS v3 filenames, plain folder names like `Projects` and `Deliverables`) scores **77.7 turns** — statistically identical to `original` (76.7) and `das` (75.3), and marginally better than `das-v2` (78.7). This holds across all 8 question types.

The address prefix in the filename provides the jump-table signal on its own. Agents doing `ls 02-Clients/02.01-ULS/Projects/` see `02.01.04-ULS-runbook-netbird-ztna-deploy.md` and immediately know the address, type, and subject — without needing the folder to also be named `02.01.04-Projects`. The folder address is redundant for navigation purposes once the filename carries the address.

**Practical implication:** You do not need to rename folder hierarchies to adopt DAS. Renaming files to the `{address}-{type}-{descriptor}` format is the entire adoption cost. Folder renames are optional and add no measurable navigation value.

### 12. Filename tag search dramatically outperforms blind discovery (-56%)

When asked to enumerate all documents for a specific client or market category, an agent using `find . -name '*-ULS-*' -type f` needs 2-3 turns vs 6-7 turns for blind folder navigation. The reduction is consistent across all four discovery questions:

| Question | tag-fn-blind | tag-fn | tag-pp | tag-fn vs blind |
|---|---|---|---|---|
| D1: ULS inventory (10 files) | 7.0 | 3.3 | 10.0 | **-3.7 turns (-53%)** |
| D2: PN inventory (4 files) | 6.3 | 3.3 | **2.7** | -3.0 turns (-48%) |
| D3: Trinidad leads (3 files) | 6.3 | 2.0 | 4.0 | **-4.3 turns (-68%)** |
| D4: Cross-client sweep | 6.7 | 3.0 | 6.0 | **-3.7 turns (-55%)** |
| **Total** | **26.3** | **11.7** | **22.7** | **-14.6 turns (-56%)** |

**Passport tag grep** (`grep -rl 'tag' .`) works when the tag string is unique (D2: PN uses `pax-nocturna`, avg 2.7 turns — wins that question). It degrades when the string is common: `uls` appears in document content, client names, and multiple passport fields, leading to false positives and extra navigation (D1: 10.0 turns — worst of all three). Filename tags are more reliable because the uppercase code's position in the filename is unambiguous.

**Note on discovery vs navigation questions:** tag-fn/tag-pp ran on 4 dedicated discovery questions (D1-D4). All other variants ran on 8 navigation questions (Q1-Q8). Aggregate comparisons in the report mix the two question sets and are apples-to-oranges — use the 3-way tag comparison in isolation.

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

**7. Use optional tags selectively — apply to out-of-context docs only.**  
Tags help targeted enumeration (Q4: -2 turns, Q8: -1.4 turns) but cost broad navigation (Q1: +4 turns, Q3: +3 turns). Apply to client/market-scoped docs that regularly surface in git log, search results, tickets, or email — where the address hierarchy is not visible. Do not tag internal admin, product, or marketing docs where in-corpus scanning is the primary access pattern. Each tagged file adds parsing cost to every `ls` scan of its folder.

**8. Filename tag search is the best discovery pattern when tags are available.**  
When an agent needs to enumerate all documents for a specific client or category without knowing where they are, `find . -name '*-TAG-*' -type f` is dramatically faster than blind folder navigation: 11.7 vs 26.3 total turns across 4 discovery questions (-56%). Passport tag grep (`grep -rl 'tag' .`) works for small targeted sets (PN: 2.7 turns) but degrades on common strings (ULS: 10.0 turns avg — `uls` appears in too many passport fields to grep reliably). Filename tags are the superior discovery path.

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
- **Corpus builders:** `~/Projects/das-nav-test/build-descriptive.py`, `~/Projects/das-nav-test/build-das-v2.py`
- **Embedding:** `~/Projects/das-nav-test/rag-test.py`
- **Report generator:** `~/Projects/das-nav-test/report.py`
- **Run data:** `~/Projects/das-nav-test/results/` (38 runs)
- **ChromaDB:** `~/Projects/sage/.claude/rag/chroma_db` — `das_nav_test_nomic`, `das_nav_test_mxbai`
