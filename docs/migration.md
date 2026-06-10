# Migrating to DAS: Converting an Existing Corpus

This guide covers how to convert an existing, non-DAS document collection into a properly
addressed DAS corpus. It focuses on three common source types: Johnny.Decimal corpora,
wiki exports (Notion, Confluence, MediaWiki), and flat folder structures.

For top-level restructuring of an existing DAS corpus, see `docs/restructuring-a-corpus.md`.
For the record format to capture a completed migration, see `docs/das-migration-convention.md`.

---

## Before you start: assess what you have

The migration effort scales with three factors:

**1. Size.** Under 200 documents: the full migration can be done in one session with manual
triage. 200-1000 documents: break into batches by source type or business area. Over 1000
documents: consider starting with a golden set (the most important 10%) and growing from there.

**2. Existing structure quality.** A well-organized JD corpus with consistent naming is a
much lighter lift than a flat folder of 800 PDFs with no naming convention. The migration
work is mostly classification - if the source has already done that work, the DAS port is
mostly mechanical.

**3. External dependencies.** If other systems reference the existing filenames or paths
(email threads, database records, shared bookmarks), plan for a transition period where both
the old and new structures coexist before the old one is retired.

---

## Migration procedure

Regardless of source type, the migration follows the same sequence:

**Phase 1: Design the address space**

Before creating any DAS nodes, design the full area and category structure on paper (or in a
scratch document). This is the highest-risk decision in a migration - you cannot renumber later.

Questions to answer:
- How many top-level areas does this corpus need? (Rule of thumb: 5-15 areas covers most
  organizational corpora; more than 20 suggests over-classification.)
- Which pattern fits this corpus? See `docs/corpus-layout-patterns.md`.
- Will any category hold more than 99 documents? If yes, consider three-digit addressing at
  that level from the start. See `docs/address-segment-width.md`.
- Should the corpus use sequential or gapped area numbering? Gapped (00, 10, 20...) if areas
  will evolve; sequential if the area set is known and stable.

Write the proposed area map down before running `das init`. Review it against the actual
source material to verify every document has a clear home.

**Phase 2: Initialize the corpus**

```bash
mkdir ~/Projects/my-corpus
cd ~/Projects/my-corpus
das init my-corpus --org ORG --tag CODE=description
```

Choose the `--naming-style` that fits the source material:
- `das-address` (default): for structured reference material and data corpora
- `slug-date`: for editorial / content corpora where publish date matters
- `custom`: for corpora with an established naming convention you want to preserve

**Phase 3: Build the address tree**

Add nodes top-down, parents before children:

```bash
das add 00 Meta "Corpus conventions and index"
das add 01 Clients "One subcategory per active client engagement"
das add 01.01 Acme-Corp "Acme Corporation - Chicago, IL"
das add 01.01.01 Contracts "MSAs, SOWs, amendments"
# ...
```

Add all areas and categories before filing any documents. This lets you verify the full
structure before committing to the address assignments.

**Phase 4: Classify and file**

Group the source documents by category. For each category:

1. Copy (not move) the source file into the appropriate DAS folder.
   - Keep the original in place until the migration is complete and verified.
   - Never modify the source file during migration - DAS requires verbatim originals for
     sourced content. The passport records provenance; the file is a clean copy.
2. Rename the file to the DAS naming convention:
   `{address}-[{TAG}-]{type}-{descriptor}.ext`
3. Add the manifest node: `das add {address} {Label} {description}`
4. Write the passport if the corpus pattern requires it.

**Phase 5: Validate**

```bash
das validate
```

Fix all errors before proceeding. Common migration errors:
- File address does not match parent folder address (wrong folder depth)
- Unknown tag (source filename had an abbreviation not in the config vocabulary)
- Folder label not Title-Cased

**Phase 6: Record the migration**

Create `das.migration.md` at the corpus root documenting what changed and why.
See `docs/das-migration-convention.md` for the format.

**Phase 7: Retire the source**

Once the migration is verified (validate clean, key documents spot-checked):
- Archive the source collection (do not delete it until you are confident nothing depends on it)
- Update any external references that pointed to the old paths

---

## Source-specific guidance

### Johnny.Decimal corpora

JD and DAS share the permanence principle, which makes JD-to-DAS migrations cleaner than
most. The key differences to handle:

**Depth:** JD uses two levels (areas and categories, written as `10.21`). DAS supports
unlimited depth. In the migration, the JD area and category map directly to the first two
DAS levels. If any JD category holds more than ~15 documents, consider adding a subcategory
level during migration rather than filing everything flat.

**Naming:** JD filenames do not carry their address. In a DAS migration, every file gets
the address prefix added. This is purely additive - the address goes at the front, the
rest of the filename can stay as the descriptor.

**Schema files:** JD has no `das.config.yaml` equivalent. The schema decisions (org code,
tag vocabulary, naming convention) must be made fresh at `das init` time.

**The JD address map:** JD addresses like `21` (area 20, category 21) map to DAS `21` directly
if you want to preserve the existing addresses. Alternatively, re-address from scratch using
a new structure that fits the corpus better. If external references exist to JD addresses,
preserve them; otherwise, redesign freely.

### Wiki exports (Notion, Confluence, MediaWiki)

Wiki exports produce a flat or loosely-nested collection of Markdown or HTML files. The
main challenges:

**No natural address space.** Wiki pages have URLs or IDs, not DAS addresses. The full
classification work must be done during migration - there is no existing structure to port.

**Unstable names.** Wiki page titles often change; some pages have no title discipline at all.
Every file gets a new DAS-compliant name during migration. The old title becomes the descriptor.

**Embedded links.** Wiki pages often reference each other by URL or page ID. After migration,
internal links will be broken. Options:
- Leave them broken (acceptable for archived content)
- Add a `see_also` field to each passport pointing to the DAS addresses of referenced documents
- Do not attempt to rewrite the links in the document body (modifies the source, which DAS
  requires verbatim for sourced content)

**Format conversion.** Export the wiki in its native format (Markdown if available). Do not
convert HTML to Markdown during migration - keep the original export format and mark the
`source` passport field accordingly. Conversion can happen later as a separate operation.

### Flat folder structures

The least-structured source type and the most common.

**Start with triage, not addressing.** Before opening `das init`, spend time grouping the
source files by topic or function. Put them in temporary grouping folders. Count the groups
and their sizes. This triage output directly informs the area/category design in Phase 1.

**Common triage mistake:** creating too many areas. If you have 300 files and 40 groupings,
most of those groupings should be categories under a smaller number of areas. Aim for
5-15 areas with multiple categories each, not 40 areas with one or two documents each.

**Undated files.** Flat folder collections often mix file types and have no date information.
The passport `created` field can be set from file system metadata during migration (use
`stat` to get the mtime), but treat this as approximate - it may reflect when the file was
copied, not when it was created. Document the uncertainty in the passport.

**Duplicates.** Flat folders frequently contain near-duplicates (slightly different versions
of the same document, with names like `final_v2`, `FINAL_FINAL`). During triage, identify
and consolidate duplicates. File only the canonical version; note the duplicates in the passport
`notes` field. Do not file multiple versions unless the version difference is significant.

---

## Partial migrations

It is acceptable to migrate a corpus in stages - port the most critical areas first, leave
the rest in the source structure until later.

When doing a partial migration:
- The DAS corpus and the source collection coexist during the transition period
- Mark the DAS corpus conventions doc clearly to note which areas are migrated and which are
  still pending
- Do not add manifest nodes speculatively for un-migrated areas - add them when the content is
  actually filed
- Track migration status in `das.migration.md` with a checklist of areas pending migration

---

## When not to migrate

Not every document collection needs to become a DAS corpus. DAS is designed for corpora
that need:
- Stable, permanent addresses (the content will be referenced externally, by agents, or over
  a long time horizon)
- Machine-readable structure (agents or tooling will navigate the corpus)
- Evolving content under a consistent schema

If the collection is a one-time export, a short-lived project, or something that no agent
will ever navigate, the DAS migration overhead may not be worth it. Consider DAS when the
corpus will be actively maintained and accessed over time.

---

*See also: `docs/das-migration-convention.md`, `docs/corpus-layout-patterns.md`,
`docs/address-segment-width.md`, `docs/restructuring-a-corpus.md`*
