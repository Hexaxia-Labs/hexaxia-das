# DAS Naming Convention Analysis

**Date:** 2026-05-28  
**Author:** Aaron Lamb  
**Status:** Design proposal — pending empirical validation (DAS v2 corpus test)  
**Feeds into:** `docs/spec.md` — future revision of filename format

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
| Date in filename | Noise. No navigation or routing value. | Noise. Makes files look stale. Accumulates over time. | Noise. Passport `created`/`modified` fields own this. |
| HXT / org prefix | Noise. Every file in a single-org corpus already belongs to that org. | Noise. | Noise. |
| Client code in filename | Redundant with folder path and address hierarchy. | Useful only when file is seen out of context (search results, git log, email). | Redundant with `das_address` in passport. |
| Passport summary | N/A (summary lives in the passport block, not the filename). | N/A. | **The actual retrieval signal.** Quality of the `summary` field determines RAG accuracy — not the filename. |

**Net conclusion:** the address and type slug earn their place. Everything else is noise or handled better elsewhere.

---

## Proposed Format

```
{address}-{type}-{descriptor}.ext
```

| Token | Rules |
|---|---|
| `{address}` | DAS dotted numeric address (e.g., `02.01.04`). Required. |
| `{type}` | Controlled vocabulary slug (see below). Required. |
| `{descriptor}` | 2-4 word kebab-case subject. No articles, conjunctions, dates, or org codes. |

### Current vs proposed

```
02.01.04-HXT-ULS-netbird-ztna-deployment-260509.md  →  02.01.04-runbook-netbird-ztna.md
07.08-HXT-hexpublish-product-spec-260426.md          →  07.08-spec-hexpublish.md
04.05.02.03-HXT-quiet-erosion-260512.md              →  04.05.02.03-post-quiet-erosion.md
03.07.02-HXT-shine-distributors-260518.md            →  03.07.02-lead-shine-distributors.md
07.07-HXT-security-compliance-product-catalog.md     →  07.07-catalog-security-compliance.md
04.06-HXT-playbook-web-discovery.md                  →  04.06-playbook-web-discovery.md
```

---

## Controlled Type Vocabulary

Hard cap at 15 types. Anything that doesn't fit forces a naming decision rather than accumulating drift.

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

## Open Questions

### 1. Client code — drop or keep?

The address scopes the client. `03.07.02-lead-shine-distributors.md` in `03-Sales/03.07-Leads/03.07.02-Trinidad/` is unambiguous in context. But in a git log, search result, or email attachment the file has no client signal without knowing the DAS map.

Options:
- **Drop entirely.** Address handles it. Cleaner filenames.
- **Keep for client-scoped docs only.** `02.01.04-ULS-runbook-netbird-ztna.md` vs `07.08-spec-hexpublish.md`.

Not yet tested empirically. Low-cost experiment: build a variant with and without client codes and compare Q4/Q5-class questions.

### 2. Does the type slug consistently improve structural orientation? CONFIRMED.

DAS v2 corpus test result: Q6 (structural orientation) dropped from 13.3 turns (das) to 9.7 (das-v2), matching the original corpus baseline of 9.7. The type slug lets agents characterise document type from `ls` output without opening files. Aggregate performance is neutral — no regression across other question types.

### 3. Folder naming — address-prefixed labels or bare descriptors?

Current: `02-Clients/02.01-ULS/02.01.04-Projects/`  
Alternative: `02-clients/02.01-uls/02.01.04-projects/` (lowercase)

Mixed-case label folders are visually distinct from files in `ls` output. Current convention is fine — no change proposed.

---

## DAS v2 Corpus Test Results

Built `Hexaxia-Technologies-DAS-v2`:
- Same content as DAS corpus
- Same passports, same manifest
- All files renamed to `{address}-{type}-{descriptor}.ext`
- 3 runs, same 8 questions

Results vs DAS:
- Aggregate turns: 78.7 vs 75.3 — neutral (within variance)
- Q6 structural orientation: **9.7 vs 13.3** — confirmed improvement (+3.6 turns, -27%)
- Q1 deep lookup: 14.3 vs 7.0 — regression (descriptor truncation; "netbird-ztna-deployment" → "netbird-ztna" loses search signal)
- All other questions: neutral

Build script: `~/Projects/das-nav-test/build-das-v2.py`

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

| Decision | Status |
|---|---|
| Drop dates from filenames | Confirmed |
| Drop HXT prefix | Confirmed |
| Keep numeric address prefix | Confirmed — proven critical |
| Add type slug | **Confirmed — DAS v2 test: Q6 13.3 → 9.7 turns, neutral aggregate** |
| Keep descriptors specific (not over-truncated) | **Confirmed — Q1 regression traced to descriptor truncation** |
| Drop client code | Open — lean toward drop, needs test |
| Controlled type vocabulary (~15) | Proposed — list above is v1 draft |
| Passport as SQL schema foundation | Noted — out of scope until naming stabilizes |
