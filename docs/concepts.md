# Hexaxia DAS Concepts

Core concepts for understanding the DAS standard.

---

## The Hexaxia DAS Address

Every node in a DAS corpus - every folder and every file - has a **DAS address**: a dotted
sequence of numeric segments (two-digit by default) that uniquely identifies its position in the hierarchy.

```
00          <- first level (area)
00.01       <- second level (category)
00.01.01    <- third level (subcategory)
00.01.01.01 <- fourth level (context)
```

Rules:
- Each segment is two or more digits; two-digit (`00` through `99`) is the default
- Segments are separated by dots
- Depth is unlimited in theory; 4 levels covers most organizational needs
- **Addresses are permanent.** Once assigned, a DAS address never changes, never gets reused,
  and never gets renumbered. If a node is retired, its address is archived - not recycled.

Think of a DAS address as an IP address for a document or folder. It is stable, machine-parseable,
and unambiguous regardless of what surrounds it.

---

## The Human Label

Every node also has a **human-readable label**: a concise, descriptive name that tells a person
what the node contains without decoding the address.

- Folder labels are Title-Cased and hyphenated: `Business-Registration`, `Q2-2026`
- File descriptors are lowercase and hyphenated: `msa-amendment`, `q2-social-brief`
- Labels are not permanent in the same sense as addresses - a label can be updated to reflect a
  renamed client or reorganized department. The address beneath it never changes.

---

## The Node Name

In the filesystem, the address and label are **fused into a single node name**. They travel
together. An agent strips the address to navigate; a human reads the label to understand.

```
{address}-{Label}/                       <- folders
{address}-[{TAG}-]{type}-{descriptor}.ext <- files (see spec.md section 5.2)
```

Examples:

```
00-Admin/
00.01-Business-Registration/
00.01.01-State-Filings/
00.01.01-contract-articles-of-incorporation.pdf
02.01.03-ACME-contract-msa-amendment.md
```

`das new <address> <type> <descriptor>` scaffolds a conformant file at an address, writing a
passport stub (with an empty `summary` to fill in) into `.md` files.

### Document Passports

A Document Passport is a per-document metadata block (address, type, status, tags, dates,
and a summary) embedded at the top of a `.md` file. The `summary` is the signal RAG uses to
route to the document. `das new` scaffolds a passport stub for new `.md` files. See
[passports.md](passports.md) for the full reference and spec section 10.2 for the
normative definition.

---

## The Corpus

A **corpus** is a Hexaxia DAS-organized document collection. Every corpus has:

- A **root directory** where all documents live
- A **config file** (`das.config.yaml`) that defines the naming schema for the corpus
- A **manifest** (`das.manifest.yaml`) that maps every address to its label and description

A corpus can be a company's full document archive, a project's working files, a client engagement
folder, or any bounded collection that needs structured, permanent addressing.

### Finding a corpus

DAS resolves addresses *inside* a corpus, but an agent first has to know which corpus to open
and where it lives on disk. That is the job of the project registry - a separate, local-only
index that maps a project slug to its filesystem path. An agent runs the registry's lookup
script with a slug to get the corpus root, then uses the manifest
and address space from there. The registry is step 0 above all in-corpus navigation; see
[project-registry.md](project-registry.md) for how it works and its relationship to DAS.

---

## Node Types

Nodes are classified by their depth in the hierarchy:

| Depth | Type | Examples |
|---|---|---|
| 1 (e.g. `00`) | area | Admin, Finance, Clients, Marketing |
| 2 (e.g. `00.01`) | category | Business-Registration, Contracts, Campaigns |
| 3 (e.g. `00.01.01`) | subcategory | State-Filings, Federal-Filings |
| 4+ (e.g. `00.01.01.01`) | context | High-specificity nodes, use deliberately |

These types are inferred automatically from address depth when you run `das add`. You do not
set them manually.

---

## das.config.yaml

The **corpus config** lives at the root of every DAS corpus. It declares the naming schema
for the entire corpus. It is written once at corpus initialization and treated as **immutable**.

```yaml
version: "1.0"
corpus: atlas-technologies
initialized: 2026-05-27
org: ATL
address_separator: "."
manifest: das.manifest.yaml
```

Fields written by `das init` today (these are the fields the `das` v0.4.0 CLI reads and writes):

| Field | Required | Description |
|---|---|---|
| `version` | Yes | Schema version of the config/manifest file format (currently `"1.0"`). This is the on-disk format version, not the tool version (`0.4.0`) or the design spec version (`v0.3`). |
| `corpus` | Yes | Unique slug for this corpus |
| `initialized` | Yes | Date the corpus was created (YYYY-MM-DD) |
| `org` | No | The corpus's namespace identifier (e.g. `ATL`), used as the federation prefix (`ATL:address`). Not added to filenames - use `tags` for per-file scoping. |
| `tags` | No | Controlled vocabulary for optional filename tags: a mapping of code (2-5 characters, starting with an uppercase letter, then uppercase letters and/or digits - e.g. `ACME`, `NW7`, `M365`) to human description. Populate at init with repeatable `das init --tag CODE=description`. Omitted entirely when no tags are defined. |
| `address_separator` | Yes | Always `.` - reserved for future federation. Do not change. |
| `manifest` | Yes | Path to the manifest file |

> **Spec vs implementation note.** The design spec ([docs/spec.md](spec.md) section 4.1, v0.3) has
> moved past the legacy `context_type` / `date_format` filename scheme: it drops dates and the context
> code from filenames and instead defines an optional `tags` vocabulary in the config plus a required
> `type` slug in filenames. As of spec v0.3 (section 4), `das init` no longer writes the legacy
> `context_type` / `date_format` fields and the `--context-type` / `--date-format` options are
> removed. Existing configs that still contain these keys continue to load - they are filtered out and
> ignored. The `tags` config field is **implemented** - the `das` CLI reads and writes it, and
> `das init --tag CODE=description` populates it. `das validate` now enforces this vocabulary: a
> filename tag that is not in the config `tags` is reported as an error (enforcement is skipped when no
> vocabulary is defined). The required filename `{type}` slug is enforced only under `das validate
> --strict`: with that flag every addressed file's `{type}` must be one of the spec 5.4 type slugs, and
> a missing or unknown type is an error (folders are exempt). Default validation does not check the
> `{type}` slug, so legacy corpora are never newly-failed.

**Changing this file after initialization is a breaking change.** Every filename and manifest
entry depends on the naming format being stable. If you must change it, rename all affected files,
rebuild the manifest, and document the migration in `das.migration.md`.

---

## das.manifest.yaml

The **manifest** is the corpus map. It is a complete registry of every address in the corpus -
its label, description, type, parent, and optional metadata.

```yaml
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

  "02.01":
    label: ACME
    description: Acme Corp - Springfield, IL
    type: category
    parent: "02"
    agent_hint: "Primary MSP client. Contracts in 02.01.01, projects in 02.01.03."
```

An agent that loads the manifest can answer "where does X live?" without traversing the
filesystem. The `agent_hint` field lets human authors prime the agent with routing context
at schema-build time.

**The manifest is the source of truth for the address space.** Update it before creating
folders. Never delete a node entry - set `deprecated: true` instead.

---

## Permanence and Deprecation

The DAS address is permanent. Once assigned, it never changes and is never recycled.

When a node is no longer active:
1. Set `deprecated: true` in the manifest
2. Keep the entry - it documents that the address existed
3. Archive or move the folder contents, but do not delete the manifest entry
4. Never reuse the address for a different node

```yaml
"02.03":
  label: OldClient
  description: Engagement ended 2025-12
  type: category
  parent: "02"
  deprecated: true
```

This rule is what makes DAS addresses safe to reference from external systems - a document
passport, a database record, or an agent's memory can reference `02.03` and know it will
always resolve to the same thing, even after the client relationship ends.

---
