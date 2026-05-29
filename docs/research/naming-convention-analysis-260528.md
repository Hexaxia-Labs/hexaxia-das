# DAS Naming Convention Analysis

**Date:** 2026-05-28  
**Author:** Aaron Lamb  
**Status:** Decisions incorporated into `docs/spec.md` v0.3  
**Feeds into:** `docs/spec.md` — decisions reflected in current spec

---

## Context

Following the nav test benchmark (see `nav-test-findings-260528.md`), three corpora were compared:

- **original** — pre-DAS mixed convention
- **descriptive** — clean alphabetical folders, `{type}-{subject}` filenames, no numeric prefixes
- **das** — current DAS format `{address}-HXT-{client}-{descriptor}-{YYMMDD}.ext`

The descriptive corpus performed 30% worse than DAS on agent navigation (99.7 vs 75.3 avg turns). This prompted a systematic analysis of what each naming element actually contributes.

---

## Signal Analysis — Three Lenses

| Element | ML / Agent | Human | RAG Hybrid |
|---|---|---|---|
| Numeric address prefix | **Critical.** Acts as jump table — agents immediately discard irrelevant areas. +30% regression without it. | Learnable. Not intuitive at first, but consistent once mapped. | Routing key via `das_address` in passport. Filename numeric prefix reinforces the signal. |
| Type slug in filename | **Helpful.** Agent can characterize doc type from `ls` without reading file. Proven in Q6-class questions. | **Immediately useful.** Scan any folder and know what you're looking at. | Appears in RAG result snippets — reinforces semantic match. |
| Optional tag (corpus vocabulary) | Three proven effects: (1) **In-folder enumeration** — small win on Q4/Q8 (+2 turns, -1.4 turns). (2) **Broad `ls` scan cost** — adds a token to every filename the agent parses; hurts Q1/Q3 (−4 turns each). (3) **Corpus-wide discovery via `find . -name '*-TAG-*'`** — dramatic win: 11.7 vs 26.3 turns (-56%) when agent uses `find`. Net: navigation cost is real; discovery benefit is large and asymmetric. | **Out-of-context readability** — git log, search results, email attachments. Useful when file travels out of its folder. | Tag codes are short and distinct — unlikely to distort RAG matching. |
| Date in filename | Noise. No navigation or routing value. | Noise. Makes files look stale. Accumulates over time. | Noise. Passport `created`/`modified` fields own this. |
| HXT / org prefix | Noise. Every file in a single-org corpus already belongs to that org. | Noise. | Noise. |
| Passport summary | N/A (summary lives in the passport block, not the filename). | N/A. | **The actual retrieval signal.** Quality of the `summary` field determines RAG accuracy — not the filename. |

**Net conclusion:** address, type slug, and optional tag earn their place. Dates and org prefix are noise handled better elsewhere. Additional classification beyond one tag belongs in the passport.

---

## Adopted Format

```
{address}-[{TAG}-]{type}-{descriptor}.ext
```

| Token | Rules |
|---|---|
| `{address}` | DAS dotted numeric address (e.g., `02.01.04`). Required. |
| `{TAG}` | One optional tag from the corpus vocabulary defined in `das.config.yaml`. Uppercase 2-5 chars. Apply when any of the following is true: (1) the file regularly surfaces out of its folder (git log, email, search results); (2) you expect agents to run corpus-wide discovery queries for this entity (e.g., "list all ULS documents"); (3) the address alone is ambiguous when the file is seen in isolation. |
| `{type}` | Controlled vocabulary slug (see below). Required. |
| `{descriptor}` | 2-4 word kebab-case subject. Specific enough to match likely search terms — do not over-truncate. No articles, conjunctions, dates, or org codes. |

### Original vs adopted

```
02.01.04-HXT-ULS-netbird-ztna-deployment-260509.md  →  02.01.04-ULS-runbook-netbird-ztna-deploy.md
07.08-HXT-hexpublish-product-spec-260426.md          →  07.08-spec-hexpublish.md
04.05.02.03-HXT-quiet-erosion-260512.md              →  04.05.02.03-post-quiet-erosion.md
03.07.02-HXT-shine-distributors-260518.md            →  03.07.02-TT-lead-shine-distributors.md
07.07-HXT-security-compliance-product-catalog.md     →  07.07-catalog-security-compliance.md
04.06-HXT-playbook-web-discovery.md                  →  04.06-playbook-web-discovery.md
```

Tag is applied selectively — client-scoped and market-scoped docs benefit; internal admin and product docs typically don't need it.

**When to apply a tag — three proven use cases:**

1. **Out-of-context readability.** The file regularly surfaces in git log, tickets, email, or search results where the folder hierarchy is not visible. The tag gives immediate context without opening the file.

2. **Corpus-wide discovery.** An agent may need to enumerate all documents for this entity across the entire corpus (e.g., "list all ULS documents"). Filename tags enable `find . -name '*-ULS-*' -type f` — a single command that returns all tagged files regardless of folder location. Discovery test result: 11.7 vs 26.3 blind turns (-56%) across 4 enumeration questions.

3. **In-folder disambiguation.** Multiple clients or market segments appear in the same folder and the agent needs to filter by client without opening each file. Small benefit (Q4: -2 turns, Q8: -1.4 turns from das-v3 test).

**When not to tag:** Internal admin, products, and marketing docs where the folder already provides unambiguous context and corpus-wide enumeration is not a use case. Each tagged file adds one parsing token to every `ls` scan of its folder — cost is modest per file but accumulates across broad navigation passes (Q1: +4 turns, Q3: +3 turns in das-v3 test).

---

## Type Vocabulary

Hard cap at 15 types — now in spec section 5.4. Anything that doesn't fit forces a naming decision rather than accumulating drift.

| Type | Use |
|---|---|
| `runbook` | Operational procedure, step-by-step execution guide |
| `plan` | Project plan or roadmap |
| `spec` | Product or technical specification |
| `design` | Design document or architecture |
| `strategy` | Business or practice strategy |
| `playbook` | Sales or marketing playbook |
| `proposal` | Client proposal |
| `contract` | Legal agreement |
| `report` | Findings, analysis, or audit output |
| `catalog` | Product or service catalog |
| `lead` | Sales lead record |
| `post` | Social media post |
| `template` | Reusable document template |
| `reference` | Reference material — informational, not actionable |
| `procedure` | Formal SOP |

---

## Resolved Questions

### 1. Client code — resolved via tag vocabulary

The original question was binary: drop the client code or keep it. The spec resolves this more cleanly with an optional tag vocabulary. Client codes are one use of the tag slot — not a special feature. A file earns a tag when any of three conditions is met: (1) it travels out of context, (2) it belongs to a set agents may need to enumerate via corpus-wide discovery, or (3) in-folder disambiguation is needed.

`02.01.04-ULS-runbook-netbird-ztna-deploy.md` — tag justified on all three counts: surfaces in git log; part of a set agents enumerate ("list all ULS docs"); and ULS co-exists with PN in the same 02-Clients folder.  
`07.08-spec-hexpublish.md` — no tag needed; product is clear from the `07.08-HexPublish` folder; no corpus-wide enumeration use case for HexPublish docs.

The tag vocabulary in `das.config.yaml` defines valid codes for the corpus. Any dimension can be a tag — client, market, product, team — as long as it's in the vocabulary.

### 2. Type slug — CONFIRMED

DAS v2 corpus test result: Q6 (structural orientation) dropped from 13.3 turns (das) to 9.7 (das-v2), matching the original corpus baseline. The type slug lets agents characterise document type from `ls` output without opening files. Aggregate performance is neutral. Type slug is now required in spec section 5.2.

### 3. Folder naming — resolved, address in folder name not required

real-v3 test (live corpus, DAS v3 filenames, plain folder names like `Projects` and `Deliverables`) scored **77.7 turns** — statistically identical to the full DAS test corpus with address-prefixed folder names. The address in the filename carries the jump-table signal on its own; the folder does not need to repeat it.

**Practical implication:** DAS adoption cost is filename renames only. Folder restructuring adds no measurable navigation value and is not required. Existing folder hierarchies with plain labels are fully compatible with DAS v3 filenames.

### 4. Tag discovery — filename tags beat passport tags for corpus-wide enumeration

Tested with three variants across 4 discovery questions (D1-D4), 3 passes each:

| Variant | Strategy | Avg turns (4 Qs) | vs blind |
|---|---|---|---|
| tag-fn-blind | Blind `ls` navigation | 26.3 | baseline |
| tag-fn | `find . -name '*-TAG-*' -type f` | 11.7 | **-56%** |
| tag-pp | `grep -rl 'tag' .` on passport blocks | 22.7 | -14% |

**Filename tag search (tag-fn) is the clear winner.** A single `find` command returns all tagged files immediately, regardless of where they are in the folder hierarchy. The agent doesn't need to navigate, open folders, or read file headers.

**Passport tag grep (tag-pp) is unreliable for common strings.** It works when the tag string is distinctive and unlikely to appear in content (`pax-nocturna`: D2 avg 2.7 turns — wins that question). It breaks when the string appears in names, content, and multiple passport fields: `uls` grep led agents to open false positives and navigate more than blind (D1: 10.0 turns — worst of three). Filename tags are unambiguous because the uppercase code's position in the filename is structural, not content-based.

**Agent tooling implication:** For tag-fn to work, the agent must have `find` available as an allowed tool and a system prompt that explains the tag convention. This is a deliberate configuration choice — not every agent gets it by default.

---

## Corpus Test Results

### DAS v2 — `{address}-{type}-{descriptor}.ext`

- Same content, passports, manifest as DAS corpus
- 3 runs, 8 questions
- Aggregate: 78.7 turns vs 75.3 das — neutral (within variance)
- Q6 structural orientation: **9.7 vs 13.3** — confirmed improvement (-27%)
- Q1 deep lookup: 14.3 vs 7.0 — regression (descriptor truncation: "netbird-ztna-deployment" → "netbird-ztna")
- All other questions: neutral

Build script: `~/Projects/das-nav-test/build-das-v2.py`

### DAS v3 — `{address}-[{TAG}-]{type}-{descriptor}.ext`

- Same as v2 with tags applied selectively: `ULS` on 02.01.xx, `PN` on 02.02.xx, `TT`/`IN` on market leads
- 3 runs, 8 questions
- Aggregate: 85.0 turns vs 78.7 das-v2 — **worse** (+8%)
- Q4 enumeration: **11.3 vs 13.0** das-v2 — tag confirms client scope from `ls`, fewer opens
- Q6 structural: **9.7** — holds das-v2 gain, no regression
- Q8 misrouting: **5.3 vs 6.7** das-v2 — tag reduces false-positive folder exploration
- Q1 direct lookup: 18.3 vs 14.3 das-v2 — tag adds parsing cost on broad scans
- Q3 cross-area: 16.7 vs 14.0 das-v2 — same effect

**Verdict:** Tag is a human/out-of-context feature, not an in-corpus navigation feature. It earns its place for docs that travel; it costs turns for docs that stay in context. Use selectively.

### Real v3 — DAS v3 filenames on live corpus, plain folder names

- Live `Hexaxia-Technologies` corpus after DAS v3 rename (56 files)
- Plain folder names (`Projects`, `Deliverables`) — no address prefix in folders
- No passports, no manifest
- 3 runs, 8 questions
- Aggregate: **77.7 turns** — statistically identical to original (76.7) and das (75.3)
- All 8 questions within normal variance of the DAS test corpus results
- Q8 misrouting: 8.3 vs 5.3 das-v3 — slight regression without passports to anchor type metadata

**Verdict:** Filename address alone is sufficient for agent navigation. Folder addresses are redundant. DAS adoption requires only file renames — existing folder hierarchy does not need to change.

### Tag Discovery — filename tags vs passport tags

- Corpus: real-v3 (tag-fn, tag-fn-blind) and DAS-v2 with passports (tag-pp)
- 3 passes × 3 variants × 4 discovery questions (D1-D4)
- D1: ULS inventory (10 files) | D2: PN inventory (4 files) | D3: Trinidad leads (3 files) | D4: cross-client sweep

| Q | tag-fn-blind | tag-fn | tag-pp | tag-fn winner? |
|---|---|---|---|---|
| D1: ULS (10 files) | 7.0 | 3.3 | 10.0 | Yes |
| D2: PN (4 files) | 6.3 | 3.3 | **2.7** | No — tag-pp wins |
| D3: Trinidad leads | 6.3 | 2.0 | 4.0 | Yes |
| D4: Cross-client | 6.7 | 3.0 | 6.0 | Yes |
| **Total** | **26.3** | **11.7** | **22.7** | |

**Verdict:** Filename tag search wins overall by a large margin. Passport tag grep wins D2 only because `pax-nocturna` is a distinctive string with no false positives. For any tag that appears in document content or short client names (e.g., `uls`), passport grep is unreliable.

---

## Forward-Looking: Passport + SQL Searches

The passport block carries structured metadata — `type`, `status`, `tags`, `das_address`, `created`, `modified`, `client`, `classification` — that maps cleanly to relational columns. As agent workflows mature, the same passport fields that drive RAG address routing today become the schema for SQL-style filtering:

```sql
SELECT das_address, title, status
FROM corpus
WHERE type = 'runbook' AND tags @> ['uls'] AND status = 'active'
```

The type vocabulary defined above is the first step toward that schema. Each controlled type becomes a discrete filter dimension. The `summary` field that drives RAG retrieval becomes the full-text column.

This is out of scope while the ML/human balance is still being calibrated — the naming convention and passport quality need to stabilize first. But the design choice to use a controlled type vocabulary (vs. freeform tags) already serves both the human readability goal today and the SQL query layer later. Worth keeping in mind when finalizing the type list.

---

## Status

All decisions incorporated into `docs/spec.md` v0.3.

| Decision | Status |
|---|---|
| Drop dates from filenames | **In spec** — passport `created`/`modified` owns this |
| Drop HXT / org prefix for single-org corpora | **In spec** — `org` field optional, noted as noise for single-org use |
| Keep numeric address prefix | **In spec** — proven critical, +30% regression without it |
| Add type slug (required) | **In spec §5.2, §5.4** — DAS v2 test: Q6 13.3 → 9.7 turns, neutral aggregate |
| Keep descriptors specific (not over-truncated) | **In spec §5.3 rule 3** — Q1 regression traced to truncation |
| Client code → optional tag vocabulary | **In spec §4, §5.2, §5.3** — corpus-defined `tags:` block, one optional tag per file. DAS v3 test: tag helps targeted enumeration (Q4 -2 turns) but costs broad navigation (Q1 +4, Q3 +3). Use selectively. |
| Controlled type vocabulary (15 types) | **In spec §5.4** — hard cap, new types require explicit addition |
| Folder address prefix not required | **Confirmed** — real-v3 test: plain folder names + DAS v3 filenames = 77.7 turns (vs 75.3 das). Filename address alone carries the signal. |
| Tag provides discovery benefit via `find` | **Confirmed** — tag discovery test: `find . -name '*-TAG-*'` = 11.7 turns vs 26.3 blind (-56%) across 4 discovery questions. Adds a third use case for tags beyond human readability and enumeration. |
| Passport as SQL schema foundation | Noted — out of scope until naming stabilizes |
