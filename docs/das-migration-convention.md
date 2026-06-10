# The das.migration.md Convention

`das.migration.md` is the corpus migration record. It documents every structural change
to a corpus's address space: area reshapes, address remappings, corpus renames, and
naming convention changes. It lives at the corpus root and is maintained alongside the
manifest and config.

---

## What belongs in das.migration.md

A migration record belongs in `das.migration.md` whenever the corpus's address space
is changed in a way that is not simply additive:

- **Corpus rename:** the `corpus` slug in `das.config.yaml` changes
- **Area reshape:** one or more areas are deprecated and their content re-addressed
- **Category split or merge:** a category is split into multiple subcategories, or two
  categories are merged into one
- **Naming convention change:** the `naming` block in `das.config.yaml` is updated
  (this is a breaking change; all existing filenames may need renaming)
- **Address remapping:** content moves from one address to another for any reason
- **Segment width change:** a level's address width is changed (two-digit to three-digit)

Additive changes - new areas, new categories, new documents under existing structure -
do not require a migration record. Those are the normal, expected append-mostly operations
that `das add` handles.

---

## What does NOT belong in das.migration.md

- The full history of document filings. That is in git.
- Non-structural changes: updating a manifest `description`, adding an `agent_hint`,
  setting `deprecated: true` on a single leaf node.
- Changes still in progress. Write the record after the migration is complete and validated.
- Design notes or rationale for the address structure. Those belong in the corpus conventions
  document at `00.01-Conventions`.

---

## Format

`das.migration.md` is a Markdown file at the corpus root. Each migration is a dated entry
in reverse chronological order (most recent first).

```markdown
# das.migration.md

Migration history for {corpus-slug}.

---

## 260601 - {Short description of the change}

**Type:** rename | reshape | split | merge | naming-change | remap | segment-width

**Reason:** One sentence explaining why this change was made.

**Changes:**

| Old address | New address | Notes |
|-------------|-------------|-------|
| 01 (deprecated) | 10 | Area renamed from Clients to Enterprise-Clients; gapped |
| 01.01 (deprecated) | 10.01 | Northstar Logistics |
| 01.01.01 (deprecated) | 10.01.01 | Contracts |

**Actions taken:**
- Deprecated all old addresses in the manifest (deprecated: true)
- Created new address nodes
- Moved files to new paths
- Updated all cross-corpus references using the old addresses

**Migration validated:** yes / no (if no: explain why and when validation will be completed)
```

The date format is `YYMMDD` to match the DAS naming convention.

---

## Where it lives

Always at the corpus root, named exactly `das.migration.md`. Not inside an addressed folder,
not in `00-Meta`. The corpus root is the right location because:
- It is immediately visible to anyone who opens the corpus root
- It is alongside `das.config.yaml` and `das.manifest.yaml`, the other corpus-level files
- Agents looking for migration context do not need to navigate the address tree to find it

If the corpus has never had a migration, `das.migration.md` does not exist. Do not create
it speculatively with empty content.

---

## Writing a retroactive migration record

If a corpus was reshaped informally (without writing a migration record at the time), write
one retroactively from the git history:

```bash
git log --all --follow --name-status -- das.manifest.yaml | head -100
```

Find the commit where addresses were deprecated and new ones added. The commit message and
diff are enough to reconstruct the record. The retroactive record is still valuable - it
documents what changed and makes it possible to resolve stale cross-corpus references.

---

## Multiple migrations

A corpus with a long history may have many migrations. All of them belong in the same file,
in reverse chronological order. Do not split migrations into separate files.

If the migration history is long enough to make the file hard to scan, add a summary table
at the top:

```markdown
## Summary of migrations

| Date   | Type    | Description                          |
|--------|---------|--------------------------------------|
| 260601 | reshape | Area 01 renumbered to 10, gapped     |
| 260115 | rename  | Corpus renamed northwind-project → relay |
```

---

## Relationship to the manifest

The manifest is the authoritative record of every address that has ever existed and its
current state. `das.migration.md` is the narrative companion: it explains why addresses
changed, what they mapped to, and what external systems need to update.

An agent that finds a deprecated manifest node should check `das.migration.md` for the
address remapping. An agent that does not find a manifest node at all (address referenced
externally but absent from manifest) should check the migration record for evidence of a
reshape.

---

*See also: `docs/restructuring-a-corpus.md`, `docs/migration.md`, `docs/federation.md`*
