# Corpus Layout Patterns

Not all DAS corpora look the same. The address structure, naming convention, and
passport shape that fit an editorial content calendar look nothing like what fits a
research data corpus. This document describes the five patterns that have emerged
in practice, when to use each, and the address strategy each one calls for.

A corpus can also combine patterns - the mixed pattern is covered last.

---

## Pattern 1: Editorial / Content

**What it is:** A corpus whose primary unit is a publishable document with a lifecycle.
Content moves through states (topic → draft → ready → published → archived) and the
corpus is managed by an editorial function.

**Canonical example:** a `content/` editorial corpus

**Characteristics:**
- Documents have a publish date that matters; the filename often carries it
- The corpus is organized by program or content type, not by subject
- A lifecycle state field in the passport drives the editorial workflow
- The naming convention is typically `slug-date` rather than `das-address`, because
  human readability and chronological sorting matter more than jump-table navigation
- An editorial agent (a content or marketing lead) manages what gets filed; a DAS agent manages
  the addressing and manifest

**Address strategy:**
- Area = program or content type (Corpus-Series, Security-Series, Standalone)
- Category = stage or channel within that program
- Sequential numbering is fine - the corpus grows one piece at a time and order is editorial,
  not structural
- Published documents move to a `Published` area; the original draft address is deprecated,
  never reused

**Passport shape additions:**
```yaml
lifecycle: draft        # topic | draft | ready | scheduled | published | archived
publish_date: ""        # YYMMDD when published
channel: []             # blog, linkedin, newsletter, etc.
```

---

## Pattern 2: Product / Corporate

**What it is:** A corpus that holds the company and product documents for a single
product or initiative. Mirrors a company knowledge base - product, architecture,
go-to-market, legal, operations.

**Canonical examples:** `Relay`, `Foundry` (the 30-70 corporate layer)

**Characteristics:**
- Areas map directly to business functions: Product, Architecture, Safety, GTM, Legal
- Documents are reference material and strategy - they evolve but do not have a publish
  lifecycle in the editorial sense
- Internal vs. public distinction matters; the `INT` tag is the practical filter
- The `edition` field (oss | ee | both) applies when the product has an open-core split
- Often starts small (a few draft docs) and grows gradually as the product matures

**Address strategy:**
- Use **gapped numbering** (00, 10, 20, 30...) from the start - new business functions
  appear over time and need clean insertion slots
- Standard area map: 00 Meta, 10 Product, 20 Architecture, 30 Safety (or the product's
  signature differentiator area), 40-60 GTM / Operations / Support, 70-80 Legal / Finance,
  90 Community (if OSS), 99 Archive
- The Relay corpus is the reference implementation for the open-core variant of this pattern

**Passport shape additions:**
```yaml
visibility: internal    # public | internal
edition: oss            # oss | ee | both (omit if no open-core split)
```

**When to add a new area:** when a new business function appears that does not fit cleanly
under an existing area. Do not stretch an area beyond its function just to avoid adding one -
the gapped numbering leaves room.

---

## Pattern 3: Data / Research Corpus

**What it is:** A corpus whose primary artifacts are data files (code, datasets,
logs, PDFs, etc.) rather than authored documents. The passport is a sidecar that
describes the artifact; the artifact itself is filed verbatim and never modified.
(For the full embedded-vs-sidecar design space, see [passport-formats.md](passport-formats.md).)

**Canonical example:** `Foundry` (the 10-20 test corpus layer)

**Characteristics:**
- The primary file is the artifact (`.nc`, `.pdf`, `.csv`); the passport `.md` is a companion
- Both files live in the same addressed subfolder: `10.02.01-Facing-Basic/`
- Every artifact must have a documented source and license - provenance is a hard constraint,
  not a nice-to-have (data can encode IP)
- A coverage matrix or catalog document at the meta level makes gaps visible
- A golden set (verified-good subset) is the ground truth for any validation use

**Address strategy:**
- Top-level areas = data type or source type (by controller dialect, by source, by category)
- Each individual artifact gets its own address and its own subfolder
- Use **sequential numbering within categories** - artifacts accumulate over time in no
  particular insertion order
- Separate sourced (10.01) from synthetic (10.02) within each type area - provenance clarity

**Passport shape additions:**
```yaml
source: ""              # URL, citation, or "SYNTHETIC - owner"
license: ""             # SPDX or plain description
clearance: internal     # public | internal
verified_good: false    # true only when explicitly confirmed
verification_method: "" # how it was verified
baseline_measurement: ""# the ground-truth metric (cycle time, accuracy, etc.)
```

**The coverage matrix:** add an `INDEX.md` at the meta level with rows = artifacts,
columns = features or dimensions of interest. Makes gaps obvious without reading every
passport. Update it whenever a new artifact is filed.

---

## Pattern 4: Agent Memory

**What it is:** A corpus that serves as a structured, persistent memory layer for agents.
Documents are not authored for humans first - they are written by or for agents as
episodic records, procedures, entity descriptions, or belief snapshots.

**Canonical example:** a dedicated `memory/` corpus holding an agent's long-term memory

**Characteristics:**
- Documents are short and structured - designed for agent recall, not human reading
- Temporal validity matters: a belief or entity record has a `valid_from` / `valid_until`
  rather than a simple `status`
- The corpus is append-mostly but with explicit invalidation: old records are deprecated,
  not deleted, because the audit trail of what an agent believed and when has its own value
- Consolidation is a first-class operation: raw episodic records are periodically summarized
  into consolidated procedural or semantic records (the "sleep" step in the hippocampus
  analogy)
- This pattern is the most dynamic of the four - new records can arrive continuously

**Address strategy:**
- Areas = memory type (Index, Identity, Semantic/Declarative, Episodic, Procedural,
  Entities, Sources, Inbox, Archive)
- The Inbox area receives new raw records; a consolidation pass moves them to their
  permanent home and assigns their permanent address
- Use **gapped numbering** - the address space evolves as the memory taxonomy matures
- The permanence rule still holds: a consolidated record at `30.01.01` stays there
  permanently; if it is superseded, it is deprecated and a new record is added

**Passport shape additions:**
```yaml
valid_from: "2026-06-05"
valid_until: ""         # blank = still valid
confidence: high        # high | medium | low
source_episode: ""      # address of the raw episode this was consolidated from
```

**Note:** this pattern is the most experimental. See [agentic-memory.md](agentic-memory.md)
for how DAS serves as the cool-storage tier for an agent's long-term memory.

---

## Pattern 5: Mixed

**What it is:** Two or more of the above patterns living in the same corpus because the
corpus serves multiple purposes and a single root makes navigation and cross-referencing
simpler than federation.

**Canonical example:** `Foundry` - Pattern 2 (corporate, areas 30-70) plus Pattern 3
(data/research corpus, areas 10-20) in the same root.

**When to use a single corpus vs. separate corpora:**

| Use one corpus | Use separate corpora |
|----------------|---------------------|
| The patterns are tightly coupled (the data IS the product's validation asset) | The patterns have independent owners or access controls |
| Cross-references between layers are frequent | One layer is public, the other is internal |
| The corpus is young and local - no federation needed yet | The corpus is already large enough that a single manifest is unwieldy |
| The layers share the same tags and passport conventions | The layers have incompatible naming conventions |

**Address strategy for mixed corpora:**

Reserve distinct address ranges for each layer so they read clearly at a glance.
The convention that has emerged in practice:

- 00 = shared Meta (conventions covering all layers, indexes)
- Low addresses (10-20) = the data / operational layer
- Mid addresses (30-70) = the corporate / product layer
- 90-98 = community / operations (if applicable)
- 99 = Archive

If the layers later need to be separated into their own corpora, the address ranges
make that split clean - each layer's addresses are already non-overlapping.

---

## Choosing a pattern

| Question | Likely pattern |
|----------|---------------|
| Is the primary artifact a publishable document with a lifecycle? | Editorial (1) |
| Is this a company / product knowledge base? | Product/Corporate (2) |
| Are the primary artifacts data files, programs, or research artifacts? | Data/Research (3) |
| Is the corpus serving as persistent agent memory? | Agent Memory (4) |
| Is it more than one of the above in a tightly coupled set? | Mixed (5) |

When in doubt, start with the simplest pattern that fits. A corpus can evolve from Pattern 2
to Pattern 5 by adding a data layer alongside the corporate layer - this is exactly what
happened with Foundry, and it was a clean addition because the address ranges did not overlap.
