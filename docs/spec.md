# Hexaxia DAS: Document Addressing Standard
## Design Specification v0.2

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

Every node in a DAS corpus - every folder and every file - has a **DAS address**: a dotted sequence of two-digit numeric segments that uniquely identifies its position in the hierarchy.

```
00          ← first level (area)
00.01       ← second level (category)
00.01.01    ← third level (subcategory)
00.01.01.01 ← fourth level (context)
```

Rules:
- Each segment is always two digits: `00`–`99`
- Segments are separated by dots
- Depth is unlimited in theory; 4 levels covers most organizational needs
- **Addresses are permanent.** Once assigned, a DAS address never changes, never gets reused, and never gets renumbered. If a node is retired, its address is archived - not recycled.

### 3.2 The Human Label

Every node also has a **human-readable label**: a concise, descriptive name in lowercase hyphenated form. The label tells a human what the node contains without needing to decode the address.

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
corpus: hexaxia-technologies
initialized: 2026-05-28
org: HXT                    # optional - omit for single-org corpora
address_separator: "."      # always "." - reserved, do not change
manifest: das.manifest.yaml

tags:                       # optional - controlled vocabulary for filename tags
  ULS: "United Life Services client"
  PN: "Pax Nocturna client"
  TT: "Trinidad market"
  IN: "Indiana market"
  LABS: "Hexaxia Labs / OSS"
  MKTG: "Marketing internal"
```

### 4.1 Configuration Fields

| Field | Required | Description |
|---|---|---|
| `version` | Yes | Hexaxia DAS spec version this corpus was initialized against |
| `corpus` | Yes | Unique slug identifying this document corpus |
| `initialized` | Yes | Date the corpus was created (YYYY-MM-DD) |
| `org` | No | Org code prepended to filenames (e.g. `HXT`). Omit for single-org corpora — adds no signal when every file belongs to the same org. |
| `tags` | No | Controlled vocabulary for optional per-file tags. Each entry is a code (2-5 uppercase characters) and a human description. Tags appear in filenames as a primary disambiguation signal. See Section 5.3. |
| `address_separator` | Yes | Always `.` - reserved for future federation use. Do not change. |
| `manifest` | Yes | Path to the corpus manifest file |

### 4.2 Schema Immutability

**Changing `das.config.yaml` after corpus initialization is a breaking change.**

Every filename, every manifest entry, every index, and every agent or tool that operates on the corpus depends on the naming format being stable. Changing `org` or the `tags` vocabulary after files exist means every filename in the corpus is now wrong relative to the schema.

If a breaking change is unavoidable:
1. Document the change and the reason in a `das.migration.md` file at the corpus root
2. Rename all affected files before updating the config
3. Rebuild the manifest
4. Notify any agents, indexes, or integrations that reference the corpus

There is no safe "quick change" to the corpus config. Treat it with the same respect as a database schema migration.

**Adding a new tag to the vocabulary is non-breaking** — existing filenames are unchanged and the new code is immediately available for new files. Renaming or removing an existing tag code is breaking.

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
| `TAG` | Optional | `tags` vocabulary in config | `ULS`, `TT`, `LABS` |
| `type` | Yes | Controlled vocabulary (see 5.4) | `runbook`, `spec`, `lead` |
| `descriptor` | Yes | Author | `netbird-ztna`, `msa-amendment` |

Examples:

```
# Client-scoped doc with tag:
02.01.04-ULS-runbook-netbird-ztna.md

# No tag needed — address is unambiguous:
07.08-spec-hexpublish.md

# Market tag:
03.07.02-TT-lead-shine-distributors.md

# OSS/Labs tag:
04.05.01.03-LABS-post-hexaxia-labs-launch.md

# Admin doc, no tag:
00-reference-company-profile.md
```

### 5.3 Naming Rules

1. Addresses always precede the human components.
2. Folder labels are Title-Cased and hyphenated (`Business-Registration`, `Q2-2026`). File descriptors are lowercase and hyphenated (`netbird-ztna`, `q2-social-brief`). No spaces, no underscores, no camelCase.
3. Descriptor is 2–4 words: concise and specific. Do not truncate words that carry query signal — a descriptor that matches likely search terms is preferable to a shorter one that doesn't.
4. File extension is always lowercase (`.md`, `.pdf`, `.docx`).
5. No sequence numbers in filenames. Formal document IDs belong in passports, not filenames.
6. TAG codes are uppercase (2–5 characters). Tags are optional — use one when it adds disambiguation signal not already provided by the address. Do not tag every file; tag files that are frequently seen out of context (search results, git log, email attachments) where the address alone is ambiguous.
7. One tag per file maximum. Multiple classification dimensions belong in the passport `tags` field.
8. Dates do not belong in filenames. Created and modified dates belong in the passport `created` and `modified` fields.

### 5.4 Type Vocabulary

Every DAS file carries a type slug as the second component after the address (and optional tag). The type communicates document intent at a glance without opening the file — useful for agents scanning `ls` output and humans navigating unfamiliar folders.

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
| `reference` | Reference material — informational, not actionable |
| `procedure` | Formal SOP |

The type in the filename is a navigation signal only. It is not a substitute for the `type` field in the document passport, which carries the authoritative value for indexing and querying.

---

## 6. The Manifest

The `das.manifest.yaml` file lives at the corpus root alongside `das.config.yaml`. It is the **corpus map** - a complete registry of every address in the corpus, its label, its description, its parent, and optional metadata.

```yaml
# das.manifest.yaml
version: "1.0"
corpus: hexaxia-technologies
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
    description: Indiana and Delaware state-level registration documents
    type: subcategory
    parent: "00.01"

  "02":
    label: Clients
    description: One subfolder per active client engagement
    type: area

  "02.01":
    label: ULS
    description: United Life Services - Indianapolis, IN
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
Level 1 (00–99)            ← Areas: major functional domains
Level 2 (00.01–00.99)      ← Categories: primary subdivisions of an area
Level 3 (00.01.01–...)     ← Subcategories: meaningful sub-groupings
Level 4 (00.01.01.01–...)  ← Context: high-specificity nodes, use deliberately
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
- Keep descriptors to 3–4 words maximum
- Treat 200-character total path length as a yellow flag; 240 as a hard stop

The 4-level soft cap naturally keeps most paths well under the 260-character limit even on legacy Windows.

---

## 8. Hexaxia DAS vs Johnny.Decimal - The Divergence

Hexaxia DAS inherits JD's core principle and diverges deliberately everywhere else.

| Dimension | Johnny.Decimal | Hexaxia DAS |
|---|---|---|
| **Depth** | 2 levels maximum (by design) | Unlimited, guided by soft caps |
| **Address range** | 10 areas, 10 categories per area | 00–99 at every level |
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
2. Addresses are two-digit segments separated by dots: `00`, `00.01`, `00.01.01`.
3. Addresses are permanent. Never renumber. Never reuse a retired address.
4. Depth is unlimited. 4 levels is the soft guidance for most corpora.

**Names**
5. Node names fuse address and label: `{address}-{Label}` for folders, `{address}-{components}.ext` for files.
6. File format: `{address}-[{TAG}-]{type}-{descriptor}.ext`. Type is required. Tag is optional — one per file, from the corpus tag vocabulary.
7. All file descriptors and folder labels are lowercase and hyphenated. TAG codes are uppercase (2–5 characters).
8. No sequence numbers in filenames. Formal document IDs belong in passports.
9. Dates do not belong in filenames. Use passport `created`/`modified` fields.
10. One tag per file. Additional classification dimensions belong in the passport.

**Schema**
11. Every corpus has a `das.config.yaml` at its root. It is written once and treated as immutable.
12. Every corpus has a `das.manifest.yaml`. It maps every address to its label, description, and parent.
13. Changing the corpus config after initialization is a breaking change. Document it. Migrate fully. Exception: adding a new tag to the vocabulary is non-breaking.
14. Retiring a node: set `deprecated: true` in the manifest. Never delete the entry. Never reuse the address.

**Depth**
13. Add a level when the current level has grown too broad and natural sub-groups exist.
14. Do not add a level just because a folder feels full - use better labels first.
15. On Windows: enable long path support and keep base corpus paths short.

---

## 10. Future Integration Points

Hexaxia DAS is designed as a standalone standard. The following integrations are in scope for future phases and were considered in the design of this spec:

### 10.1 Agent Navigation

The `das.manifest.yaml` is the foundation for agent navigation. An AI agent that loads the manifest can answer "where does X live?" without traversing the filesystem. The `agent_hint` field on manifest nodes allows human authors to prime the agent with routing context at schema-build time. Full agent navigation spec is deferred.

### 10.2 Document Passports

A Document Passport is a portable metadata container for individual documents. The DAS address is a natural primary key for passports - every document with a DAS address can carry a passport that includes that address as its location identifier. This makes documents queryable by address in a passport index without filesystem traversal. Document Passport integration spec is deferred.

### 10.3 Federation

The `address_separator` field in `das.config.yaml` is reserved for future federation support. When multiple Hexaxia DAS corpora need to be addressed together (e.g. across Hexaxia Technologies, Hexaxia AI, and Hexaxia Media), an org-prefix scheme will scope addresses to their origin corpus. Federation spec is deferred.

---

*Hexaxia DAS v0.2 | Hexaxia Technologies | 2026-05-28*
