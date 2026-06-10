# Hexaxia DAS: Document Addressing Standard
## Design Specification v0.3

**Date:** 2026-05-28
**Status:** Draft
**Author:** Aaron Lamb / Hexaxia Technologies

---

## 1. Overview

Hexaxia DAS (Document Addressing Standard) is a document organization standard designed for large, growing corpora where the original Johnny.Decimal methodology reaches its structural limits. It preserves JD's most important idea - **numbers are permanent** - and builds a complete addressing system around it: deeper hierarchy, a machine-readable manifest, a corpus-level configuration schema, and a naming convention that is both human-readable and agent-navigable.

Hexaxia DAS is intended as a POC and foundation for a broader ecosystem that will eventually include AI agent navigation and document identity (passports). The standard is designed with those futures in mind but does not require them to be useful today.

---

## 2. The Problem With JD at Scale

Johnny.Decimal was designed for personal file organization. Its two-level limit - one area, one category - is a deliberate constraint that keeps individual navigation fast and shallow. For a single person managing a personal file system, this is a feature.

At organizational scale the constraint becomes a ceiling:

- A company with 10 active clients, 6 service lines, 5 internal departments, and 4+ years of documents cannot fit meaningfully into 10 areas of 10 categories each.
- As corpora grow, the two-level limit forces either bloated categories (too many files in one place) or artificial top-level splits that break the "one home per thing" rule.
- Standard JD has no machine-readable schema. An agent navigating a JD corpus has no way to understand the address space without traversing every folder in the tree.
- JD provides no standard for how filenames relate to their location in the hierarchy.

DAS addresses all of these. It is not a replacement for personal JD use - it is an extension for when JD's constraints are the problem, not the solution.

---

## 3. Core Concepts

### 3.1 The Hexaxia DAS Address

Every node in a DAS corpus - every folder and every file - has a **DAS address**: a dotted sequence of numeric segments (two-digit by default) that uniquely identifies its position in the hierarchy.

```
00          ← first level (area)
00.01       ← second level (category)
00.01.01    ← third level (subcategory)
00.01.01.01 ← fourth level (context)
```

Rules:
- Each segment is two or more digits; two-digit (`00`-`99`) is the default. See §7.6 on widening.
- Segments are separated by dots
- Depth is unlimited in theory; 4 levels covers most organizational needs
- **Addresses are permanent.** Once assigned, a DAS address never changes, never gets reused, and never gets renumbered. If a node is retired, its address is archived - not recycled.

### 3.2 The Human Label

Every node also has a **human-readable label**: a concise, descriptive name. Folder labels are Title-Cased and hyphenated (`Business-Registration`); file descriptors are lowercase and hyphenated (`articles-of-incorporation`). The label tells a human what the node contains without needing to decode the address.

Labels are not permanent in the same sense as addresses - a label can be updated to reflect a renamed client or reorganized department. But the address beneath it never changes.

### 3.3 The Node Name

In the filesystem, the address and label are **fused into a single node name**. They travel together. An agent strips the address to navigate; a human reads the label to understand.

```
{address}-{Label}               ← folders
{address}-{components}.ext      ← files (see Section 5)

Examples:
00-Admin/
00.01-Business-Registration/
00.01.01-State-Filings/
04-Marketing/
04.03-Campaigns/
04.03.02-Q2-2026/
```

---

## 4. The Corpus Configuration

Each DAS corpus has a single configuration file at its root: `das.config.yaml`. This file declares the naming schema for the entire corpus. It is written once at corpus initialization and treated as **immutable**.

```yaml
# das.config.yaml
version: "1.0"
corpus: atlas-technologies
initialized: 2026-05-28
org: ATL                    # optional - omit for single-org corpora
address_separator: "."      # always "." - reserved, do not change
manifest: das.manifest.yaml

tags:                       # optional - controlled vocabulary for filename tags
  ACME: "Acme Corp client"
  GBX: "Globex client"
  EU: "European market"
  AMER: "Americas market"
  OSS: "Open-source / community"
  MKTG: "Marketing internal"

naming:                     # optional - the corpus's declared filename convention
  style: das-address        # das-address (default) | slug-date | custom
  pattern_draft:     "{address}-[{TAG}-]{type}-{descriptor}.{ext}"
  pattern_published: "{address}-[{TAG}-]{type}-{descriptor}-{YYMMDD}.{ext}"
  description: >
    Address-first for agent navigation; the publish date is added only at promote.
```

### 4.1 Configuration Fields

| Field | Required | Description |
|---|---|---|
| `version` | Yes | On-disk schema (file format) version of the config/manifest, currently `"1.0"`. Distinct from the tool version and the design spec version. |
| `corpus` | Yes | Unique slug identifying this document corpus |
| `initialized` | Yes | Date the corpus was created (YYYY-MM-DD) |
| `org` | No | The corpus's namespace identifier (e.g. `ATL`), used as the federation prefix (`ATL:address`) and origin declaration. Not a filename component - use `tags` for per-file scoping. Omit for local or single-org corpora. |
| `tags` | No | Controlled vocabulary for optional per-file tags. Each entry is a code (2-5 characters, starting with an uppercase letter, then uppercase letters and/or digits) and a human description. Tags serve three purposes: out-of-context readability, corpus-wide discovery via `find . -name '*-TAG-*'`, and in-folder disambiguation. See §5.3 rule 6. |
| `naming` | No | The corpus's declared filename convention. Omit it and the corpus is treated as `das-address` (the default address-first rules). Declare it to record the convention as one machine-readable source of truth, to drive `das new` generation, and (for a non-address `style`) to make `das validate` enforce a deviating convention. See §5.5 and `docs/corpus-conventions.md`. |
| `address_separator` | Yes | Always `.` - reserved for future federation use. Do not change. |
| `manifest` | Yes | Path to the corpus manifest file |

The `naming` block (when present) carries:

| Sub-field | Required | Description |
|---|---|---|
| `style` | Yes | `das-address` (the default address-first rules), `slug-date` (legacy slug-first files with no address prefix), or `custom` (a corpus-specific pattern). |
| `pattern_draft` | Yes | The canonical filename template for draft files. Tokens: `{address}` `{TAG}` `{type}` `{descriptor}` `{slug}` `{YYMMDD}` `{ext}`. An optional run is bracketed, e.g. `[{TAG}-]`. |
| `pattern_published` | No | The template once a file is promoted/published, usually `pattern_draft` plus a `{YYMMDD}` publish date. Omit it for a corpus with no draft/published lifecycle. |
| `description` | No (Yes by convention when `style` is not `das-address`) | The justification for the convention. Deviating from address-first costs the navigation signal; recording why makes the tradeoff reviewable. |

### 4.2 Schema Immutability

**Changing `das.config.yaml` after corpus initialization is a breaking change.**

Every filename, every manifest entry, every index, and every agent or tool that operates on the corpus depends on the naming format being stable. Changing `org` or the `tags` vocabulary after files exist means every filename in the corpus is now wrong relative to the schema.

If a breaking change is unavoidable:
1. Document the change and the reason in a `das.migration.md` file at the corpus root
2. Rename all affected files before updating the config
3. Rebuild the manifest
4. Notify any agents, indexes, or integrations that reference the corpus

There is no safe "quick change" to the corpus config. Treat it with the same respect as a database schema migration.

**Adding a new tag to the vocabulary is non-breaking** - existing filenames are unchanged and the new code is immediately available for new files. Renaming or removing an existing tag code is breaking.

---

## 5. Naming Convention

### 5.1 Folders

```
{address}-{Label}/

00-Admin/
04-Marketing/
04.03-Campaigns/
04.03.02-Q2-2026/
04.03.02.01-Instagram/
```

- Label is title-cased, hyphenated
- Address always precedes label

### 5.2 Files

```
{address}-[{TAG}-]{type}-{descriptor}.ext
```

Components:

| Component | Required | Governed by | Example |
|---|---|---|---|
| `address` | Yes | Always | `02.01.03` |
| `TAG` | Optional | `tags` vocabulary in config | `ACME`, `TT`, `LABS` |
| `type` | Yes | Controlled vocabulary (see 5.4) | `runbook`, `spec`, `lead` |
| `descriptor` | Yes | Author | `netbird-ztna`, `msa-amendment` |

Examples:

```
# Client-scoped doc with tag:
02.01.04-ACME-runbook-netbird-ztna.md

# No tag needed - address is unambiguous:
07.08-spec-publishing-tool.md

# Market tag:
03.07.02-AMER-lead-widget-distributors.md

# OSS tag:
04.05.01.03-OSS-post-launch-announcement.md

# Admin doc, no tag:
00-reference-company-profile.md
```

### 5.3 Naming Rules

1. Addresses always precede the human components.
2. Folder labels are Title-Cased and hyphenated (`Business-Registration`, `Q2-2026`). File descriptors are lowercase and hyphenated (`netbird-ztna`, `q2-social-brief`). No spaces, no underscores, no camelCase.
3. Descriptor is 2-4 words: concise and specific. Do not truncate words that carry query signal - a descriptor that matches likely search terms is preferable to a shorter one that doesn't.
4. File extension is always lowercase (`.md`, `.pdf`, `.docx`).
5. No sequence numbers in filenames. Formal document IDs belong in passports, not filenames.
6. TAG codes are 2-5 characters: they **must start with an uppercase letter**, then carry uppercase letters and/or digits (grammar `^[A-Z][A-Z0-9]{1,4}$`). `ACME`, `GBX`, `EU`, `NW7`, `M365` are all valid; `868` (all digits) and `acme` (lowercase) are not. Tags are optional - apply one when any of the following is true:
   - **Out-of-context readability:** the file regularly surfaces in git log, search results, tickets, or email where the folder hierarchy is not visible, and the address alone is ambiguous to a human.
   - **Corpus-wide discovery:** an agent may need to enumerate all documents for this entity across the full corpus. Filename tags enable `find . -name '*-TAG-*' -type f` - a single command that returns every tagged file regardless of folder location. Benchmark result: 11.7 vs 26.3 turns (-56%) for discovery queries when agents use this pattern.
   - **In-folder disambiguation:** multiple clients or market segments appear in the same folder and the agent needs to filter by scope without opening each file.

   **Use case - tags scope a file to a client, market, org, or brand/product.** A tag identifies *whose* or *which entity's* file this is. Real brand and product codes commonly contain digits, so the grammar admits them: `M365` and `O365` (Microsoft 365 / Office 365 markets), `S3` (an AWS service area), `NW7` (a product code). The two boundary characters keep the three filename tokens unambiguous to the parser:
   - The **leading uppercase letter** separates a tag from a numeric **address** segment. An address segment is all digits (`02`, `04`); a tag can never be all digits, so `00.01.04-NW7-...` parses `NW7` as the tag, while a hypothetical `00.01.04-868-...` could never be read as one.
   - The **lowercase** form of the **type** slug (§5.4) separates it from a tag. The first post-address token is the tag only if it starts with an uppercase letter; a lowercase first token (`runbook`, `reference`) is the type, meaning the file carries no tag.

   Do not tag broadly. Each tagged file adds one parsing token to every `ls` scan of its folder - this is measurably costly on broad navigation passes (+4 turns on direct lookup, +3 turns on cross-area queries in benchmark tests). Internal admin, product, and marketing docs where the folder already provides unambiguous context do not need tags.
7. One tag per file maximum. Multiple classification dimensions belong in the passport `tags` field.
8. Dates do not belong in filenames. Created and modified dates belong in the passport `created` and `modified` fields.

### 5.4 Type Vocabulary

Every DAS file carries a type slug as the second component after the address (and optional tag). The type communicates document intent at a glance without opening the file - useful for agents scanning `ls` output and humans navigating unfamiliar folders.

The type vocabulary is a **hard-capped controlled list**. Any document that doesn't fit an existing type forces a naming decision rather than accumulating informal drift. New types require explicit addition to this table.

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
| `reference` | Reference material - informational, not actionable |
| `procedure` | Formal SOP |
| `email` | Correspondence record - a sent or received message captured as a document |
| `log` | Time, activity, or change record kept over a period |

The type in the filename is a navigation signal only. It is not a substitute for the `type` field in the document passport, which carries the authoritative value for indexing and querying.

### 5.5 Declared Conventions and Deviations

The address-first format in §5.1-5.4 is the default and the recommended convention for every corpus - the leading numeric address is the jump-table signal agents use to discard irrelevant areas without opening a file. A corpus may **declare** a different convention in the `naming` block of `das.config.yaml` (§4). Declaration is a deliberate, reviewable choice, not drift: the convention is recorded in one machine-readable place, justified in `description`, enforced by `das validate`, and generated by `das new`.

- **`das-address`** (the default, and whenever no `naming` block is present): `das validate` applies the §5.1-5.4 address rules unchanged. This is the benchmark-optimal convention. The composed form `{address}-{type}-{slug}-{YYMMDD}.ext` is still address-first - the date sits inside the descriptor and validates as-is.
- **`slug-date` / `custom`**: a deviation for corpora with a different goal (e.g. legacy slug-first published editorial content with no address prefix). `das validate` compiles the declared `pattern_draft` and `pattern_published` to a regex and checks each non-skipped **file** name against them. Folders remain address-based regardless: the address jump-table is a property of the corpus folder structure, not of file naming. Deviating from address-first trades away the filename jump-table and the manifest cross-check; do it only when an external constraint or a documented goal requires it.

The full rationale, the layered declare/discover/validate/generate model, the date-churn rule for draft vs published files, and worked examples are in `docs/corpus-conventions.md`.

---

## 6. The Manifest

The `das.manifest.yaml` file lives at the corpus root alongside `das.config.yaml`. It is the **corpus map** - a complete registry of every address in the corpus, its label, its description, its parent, and optional metadata.

```yaml
# das.manifest.yaml
version: "1.0"
corpus: atlas-technologies
updated: 2026-05-27

nodes:
  "00":
    label: Admin
    description: Company governance - legal, compliance, insurance, registrations
    type: area

  "00.01":
    label: Business-Registration
    description: Incorporation certificates, jurisdiction filings, company numbers
    type: category
    parent: "00"

  "00.01.01":
    label: State-Filings
    description: State-level registration and incorporation documents
    type: subcategory
    parent: "00.01"

  "02":
    label: Clients
    description: One subfolder per active client engagement
    type: area

  "02.01":
    label: ACME
    description: Acme Corp - Springfield, IL
    type: category
    parent: "02"
    agent_hint: "Primary MSP client. Contracts in 02.01.01, active projects in 02.01.03, correspondence in 02.01.02."

  "04":
    label: Marketing
    description: Brand, campaigns, content, and SEO
    type: area

  "04.03":
    label: Campaigns
    description: Active and archived campaign materials
    type: category
    parent: "04"

  "04.03.02":
    label: Q2-2026
    description: Q2 2026 campaign assets
    type: subcategory
    parent: "04.03"
```

### 6.1 Manifest Fields

| Field | Required | Description |
|---|---|---|
| `label` | Yes | Human-readable name for this node |
| `description` | Yes | One-sentence description of what belongs here |
| `type` | Yes | `area`, `category`, `subcategory`, `context`, `file` |
| `parent` | No (root nodes only) | DAS address of the parent node |
| `agent_hint` | No | Optional routing guidance for agents - what's here, what to look for |
| `deprecated` | No | If `true`, this address is retired. Never reuse it. |

### 6.2 Manifest Maintenance

The manifest is the source of truth for the address space. It should be updated whenever:
- A new folder is created (add the node entry before creating the folder)
- A node is deprecated (set `deprecated: true`, never delete the entry)
- An `agent_hint` is refined based on actual usage patterns

The manifest can be maintained manually or by tooling. In either case, the manifest must always reflect the current state of the corpus - a stale manifest is worse than no manifest.

Reshaping the top level or renaming the whole corpus is a larger operation than routine maintenance. See `docs/restructuring-a-corpus.md` for when it is safe (a young, uncalcified corpus) and how to do it: rename via `git mv`, re-address the moved docs, record the reshape in `das.migration.md`, and deprecate rather than delete once the corpus is mature.

Different corpus purposes call for different area structures. See `docs/corpus-layout-patterns.md` for the four patterns that have emerged in practice (editorial/content, product/corporate, data/research, agent memory) and how to combine them in a single corpus. For the operational lifecycle - batch filing, adding areas over time, the promotion path from local to shared, and the manual ETL ingestion procedure - see `docs/dynamic-corpus-management.md`.

---

## 7. Depth Model

Hexaxia DAS imposes no hard depth limit. A corpus can go as many levels deep as the content genuinely requires. However, depth should be **earned**, not assumed.

### 7.1 When to Add a Level

Add a level when:
- The current node has grown beyond ~20 direct children and they fall into clear natural groups
- You need to distinguish between meaningfully different sub-types - not just more items of the same type
- A new team member couldn't reliably predict which node to navigate to without finer subdivision

### 7.2 When Not to Add a Level

Do not add a level when:
- You only have a handful of documents that could be named more distinctly instead
- You're adding depth because the folder "feels full"
- The new level would only ever contain one or two children

### 7.3 Soft Guidance by Level

```
Level 1 (00-99)            ← Areas: major functional domains
Level 2 (00.01-00.99)      ← Categories: primary subdivisions of an area
Level 3 (00.01.01-...)     ← Subcategories: meaningful sub-groupings
Level 4 (00.01.01.01-...)  ← Context: high-specificity nodes, use deliberately
Level 5+                   ← Scrutinize carefully - is the area above too broad?
```

4 levels covers the needs of most organizations. A 5th level is a yellow flag. A 6th level is a signal that something upstream is too wide and should be restructured.

### 7.4 Path Length Considerations

DAS addresses are compact - a 4-level address (`04.03.02.01`) is only 14 characters. The practical path length concern comes from combining a long base corpus path with deep nesting and verbose descriptors.

| Platform | Path limit | Risk level |
|---|---|---|
| Linux | 4,096 bytes | Negligible |
| macOS | 1,024 bytes | Negligible |
| Windows (legacy MAX_PATH) | 260 chars | Real - tools and git may fail |
| Windows (long paths enabled) | 32,767 chars | Fine, but requires registry opt-in |

**Guidance for Windows corpora:**
- Enable long path support at corpus setup (Windows 10 1607+, Group Policy or registry)
- Keep the corpus base path short (e.g. `C:\Docs\` not `C:\Users\firstname\Documents\Company\`)
- Keep descriptors to 3-4 words maximum
- Treat 200-character total path length as a yellow flag; 240 as a hard stop

The 4-level soft cap naturally keeps most paths well under the 260-character limit even on legacy Windows.

### 7.5 Numbering Strategy: Sequential vs Gapped

When you allocate addresses at a level - areas especially - you choose how densely to number.
Both schemes are valid: the address grammar accepts any two-digit value, so `01` and `10` are
equally legal. The choice trades against one fixed rule: **addresses are permanent and are
never renumbered** (sections 6 and 9). You are not numbering for today; you are numbering for
every insertion you cannot yet foresee.

**Sequential** - `00, 01, 02, 03 …`. Dense and tidy. Best when the set at this level is known
and stable, or when you are matching an existing house convention. The cost: there is no room
to insert a new node *between* two existing ones. Because you cannot renumber, an area that
later belongs logically between `01` and `02` has to be appended at the next free number
(`08`), out of reading order. Logical order and numeric order drift apart over time.

**Gapped** - `00, 10, 20, 30 …`, leaving a gap of ten between entries. Less dense, but it
preserves the ability to insert a new node in its logical position forever: a new area between
`10-Product` and `20-Architecture` slots in at `15` without touching anything else. This is the
original Johnny.Decimal instinct - JD numbers its areas in ranges (10-19, 20-29) for exactly
this reason (section 8). Best for a greenfield or still-evolving taxonomy whose set you expect
to grow.

**Guidance:**

- Choose per corpus, deliberately, and write down which scheme you used. Inconsistency within
  `00-Corpora` is not a bug, but an undeclared switch reads as a mistake.
- If you gap, gap the level you expect to grow (usually areas); you can still number the
  children sequentially under each parent. Mixing is fine as long as it is intentional.
- Prefer **sequential** when the area set is fixed - for example a division corpus that runs a
  known `00-Admin … 99-Archive` - and you value density and consistency with sibling corpora.
- Prefer **gapped** when you are inventing the taxonomy and want logical-position insertion
  headroom under permanent addresses.
- Reserve a high area (commonly `99-Archive`) regardless of scheme; it always sorts last.

**In practice.** A division corpus and an editorial corpus
number areas sequentially because their top-level set was known up front. `Northwind-Project`
(a fictional young product corpus used in these examples) numbers areas in gaps (`00, 10, 20, …`) because it is a young product taxonomy expected to grow
new top-level areas later - a marketing or integrations area, say - that should slot into their
logical position rather than be bolted onto the end. The permanence rule is what makes the
difference matter: with sequential numbering, the only way to honor a later logical insertion is
to break reading order; with gapped numbering, the slot is already waiting.

### 7.6 Segment Width: Two, Three, or Four Digits

The default DAS segment is two digits (`00`-`99`, 100 slots per level). This is the right
default for the vast majority of corpora. It is not the only valid choice.

**Two digits (`00`-`99`):** default. 100 slots per level is sufficient for almost any corpus
at any depth. If a category is growing toward 99 children, that is nearly always a signal to
add a sublevel rather than widen the segment. Two digits also keeps addresses short and
human-readable - `10.02.07` is scannable; `010.002.007` is not.

**Three digits (`000`-`999`):** 1,000 slots per level. The right choice when a specific
category will genuinely hold more than 99 children and those children do not subdivide
cleanly into sub-categories. The canonical case is a **data or research corpus at scale** -
for example, a sensor-telemetry corpus expected to eventually hold several hundred readings under
a single device category, or a document archive ingesting an entire filing system where
one folder legitimately holds 200+ items. Three digits is a deliberate choice for a specific
level, not a global setting - you can use three-digit addressing at the program level
(`10.001`, `10.002`, …) while keeping two-digit area addresses (`10`, `20`).

**Four digits (`0000`-`9999`):** 10,000 slots per level. Warranted only for very large
automated ingestion pipelines where a single category will hold thousands of items and
further subdivision is either impractical or semantically meaningless. A corpus at this
scale is almost certainly being populated by a tool (ETL) rather than by hand.

**Mixing widths deliberately:** widths can differ between levels in the same corpus, as long
as the choice is declared in the corpus conventions and applied consistently within each level.
An area level at two digits and a program level at three digits is a reasonable mix.
What is not valid is mixing two-digit and three-digit addresses *at the same level* within
the same parent - that makes addresses ambiguous to sort and confusing to read.

**The rule:** declare segment width in `00.01-Conventions` at corpus init. Two digits unless
you have a concrete, known reason for more. If you pick three or four, write down why - the
reason is almost always "this category will hold N > 99 items" and that constraint should be
recorded so future maintainers do not wonder.

For a fuller discussion including implementation considerations, see
`docs/address-segment-width.md`.

---

## 8. Hexaxia DAS vs Johnny.Decimal - The Divergence

Hexaxia DAS inherits JD's core principle and diverges deliberately everywhere else.

| Dimension | Johnny.Decimal | Hexaxia DAS |
|---|---|---|
| **Depth** | 2 levels maximum (by design) | Unlimited, guided by soft caps |
| **Address range** | 10 areas, 10 categories per area | 00-99 at every level |
| **Filename role** | Human navigation only | Address is a machine-parseable coordinate |
| **Schema artifact** | None - convention only | `das.config.yaml` + `das.manifest.yaml` |
| **Naming convention** | Informal, per-user | Formally defined, corpus-configured, immutable |
| **Agent-ready** | No | Yes - manifest provides full corpus map in one read |
| **Multi-entity** | No | Deferred but designed for (org prefix, federation path) |
| **Immutability scope** | Numbers permanent | Numbers + full naming schema permanent |

JD's two-level limit is not a flaw - for personal use it is exactly right. Hexaxia DAS diverges because organizational corpora have different requirements: more depth, more structure, machine-readable schema, and eventual agent participation. Hexaxia DAS keeps the one principle that matters at any scale - **numbers are permanent** - and builds a complete standard around it.

---

## 9. Rules Summary

**Addresses**
1. Every node gets a DAS address. No exceptions.
2. Addresses are dotted numeric segments, two-digit by default: `00`, `00.01`, `00.01.01`.
3. Addresses are permanent. Never renumber. Never reuse a retired address.
4. Depth is unlimited. 4 levels is the soft guidance for most corpora.

**Names**
5. Node names fuse address and label: `{address}-{Label}` for folders, `{address}-{components}.ext` for files.
6. File format: `{address}-[{TAG}-]{type}-{descriptor}.ext`. Type is required. Tag is optional - one per file, from the corpus tag vocabulary. Apply when the file travels out of context, belongs to an entity set agents may need to enumerate, or needs in-folder disambiguation. See §5.3 rule 6 for full criteria.
7. File descriptors are lowercase and hyphenated; folder labels are Title-Cased and hyphenated. TAG codes are 2-5 characters, starting with an uppercase letter, then uppercase letters and/or digits (`^[A-Z][A-Z0-9]{1,4}$`) - e.g. `ACME`, `NW7`, `M365`.
8. No sequence numbers in filenames. Formal document IDs belong in passports.
9. Dates do not belong in filenames. Use passport `created`/`modified` fields.
10. One tag per file. Additional classification dimensions belong in the passport.

**Schema**
11. Every corpus has a `das.config.yaml` at its root. It is written once and treated as immutable.
12. Every corpus has a `das.manifest.yaml`. It maps every address to its label, description, and parent.
13. Changing the corpus config after initialization is a breaking change. Document it. Migrate fully. Exception: adding a new tag to the vocabulary is non-breaking.
14. Retiring a node: set `deprecated: true` in the manifest. Never delete the entry. Never reuse the address.

**Depth**
15. Add a level when the current level has grown too broad and natural sub-groups exist.
16. Do not add a level just because a folder feels full - use better labels first.
17. On Windows: enable long path support and keep base corpus paths short.

---

## 10. Future Integration Points

Hexaxia DAS is designed as a standalone standard. The following integrations are in scope for future phases and were considered in the design of this spec:

### 10.1 Agent Navigation

The `das.manifest.yaml` is the foundation for agent navigation. An AI agent that loads the manifest can answer "where does X live?" without traversing the filesystem. The `agent_hint` field on manifest nodes allows human authors to prime the agent with routing context at schema-build time. Full agent navigation spec is deferred.

**Filename tags as a discovery primitive.** When a corpus has tagged files and agents have `find` available, `find . -name '*-TAG-*' -type f` provides corpus-wide enumeration in a single command - no manifest required, no folder traversal needed. Benchmark result: -56% turns vs blind folder navigation on discovery queries. This pattern works today without any additional infrastructure; the tag vocabulary in `das.config.yaml` is the only prerequisite. Agent system prompts should explain the tag convention and when to use `find` vs `ls`.

### 10.2 Document Passports

A Document Passport is a portable metadata container for an individual document. The DAS address is the passport's primary key, making documents queryable by address without filesystem traversal.

In a Markdown file the passport is a YAML block inside a leading HTML comment, before the first heading:

```markdown
<!--
passport:
  title: "NetBird ZTNA Deployment Runbook"
  type: runbook
  status: active
  tags: [ACME, NETBIRD]
  das_address: "02.01.04"
  created: "2026-05-09"
  modified: "2026-05-28"
  summary: "Six-phase runbook to deploy NetBird ZTNA for Acme Corp (ACME).
            Current blockers: firewall ports 51820/UDP pending ACME IT approval; MFA
            enrollment for 3 admins; UAT sign-off deferred to May 30."
-->

# NetBird ZTNA Deployment Runbook
```

| Field | Required | Meaning / rules |
|---|---|---|
| `das_address` | Yes | The document's DAS address. Primary key / location identifier (section 10.2). Must match the file's address. |
| `type` | Yes | Authoritative document type. Controlled vocabulary - the same 17 type slugs as filenames (section 5.4). The filename type slug is a navigation echo; this field is authoritative for indexing. |
| `status` | Yes | Lifecycle state: `draft`, `active`, `deprecated`, or `archived`. |
| `title` | Yes | Human-readable title, specific enough to surface in search. |
| `summary` | Yes (field present) | 2-5 sentences. The entire RAG routing signal. Content rules in `writing-passport-summaries.md`. May be empty in a `draft` but an `active` document must fill it (see lifecycle). |
| `tags` | No | List of tag codes from the corpus `tags` vocabulary (`das.config.yaml`, section 4). A passport MAY carry multiple tags even though a filename carries at most one (section 5.3 rules 6-7). |
| `created` | No | Creation date, `YYYY-MM-DD`. |
| `modified` | No | Last-modified date, `YYYY-MM-DD`. |

Lifecycle: `draft` (newly created, e.g. by `das new`; summary may be empty) -> `active` (in use; summary required) -> `deprecated` (superseded, retained, dropped from primary navigation) -> `archived` (retired).

Passports are currently defined for Markdown files only. Passport storage for non-Markdown documents is deferred and will be specified separately. For a full guide with examples, see `docs/passports.md`.

### 10.3 Federation

The `address_separator` field in `das.config.yaml` is reserved for future federation support. When multiple Hexaxia DAS corpora need to be addressed together (e.g. across a company's division, content, and research corpora), an org-prefix scheme will scope addresses to their origin corpus. Federation spec is deferred.

---

*Hexaxia DAS v0.3 | Hexaxia Technologies | 2026-05-28*
