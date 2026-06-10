# Dynamic Corpus Management

How to handle a corpus that is actively changing: adding programs or documents in
batches, evolving the area structure as the corpus grows, knowing when a reshape is
still cheap vs. when it is too late, and moving a corpus from local development to
a shared or published state.

This document is about the operational lifecycle of a corpus after it is initialized.
For the initial layout choice, see `corpus-layout-patterns.md`. For top-level structural
reshapes, see `restructuring-a-corpus.md`.

---

## The corpus lifecycle

A corpus moves through three broad states:

**Young** - recently initialized, all local, few or no external references to addresses.
Reshaping is cheap. Addresses are permanent in principle but nothing depends on them yet.
This is the time to fix a wrong framing, restructure areas, or rename the corpus entirely.

**Active** - the corpus is in regular use, addresses are referenced in other documents or
by tooling, and the manifest is growing. Reshaping is costly. New areas are added at
the edges; existing areas are grown, never renumbered. The deprecate-and-add pattern
governs retired content.

**Mature** - the corpus is published, federated, or used by external agents. The address
space is effectively frozen. Structural changes require a formal migration record and
explicit deprecation.

The key question at any moment: **which state is this corpus in?** If you are not sure,
check for external references. No external references = still young enough to reshape.

---

## Adding content: the append-mostly pattern

Most of a corpus's lifecycle is append-mostly: new documents or artifacts arrive, get
addressed, and are filed. The steps are the same regardless of how many arrive at once.

**For a single document:**

1. Pick the correct category address. If no category fits cleanly, consider whether a
   new one is needed (see "When to add an area" below).
2. Assign the next sequential address within that category: `das add`.
3. Create the subfolder: `{address}-{Title-Cased-Label}/`.
4. Write or place the file with the correct naming convention for this corpus.
5. Write the passport if the corpus uses sidecar passports (data/research pattern).
6. `das validate` - fix any errors before committing.

**For a batch (many documents at once):**

The same steps, but run sequentially per document. Do not batch-assign addresses
speculatively; assign each one at filing time so the manifest stays the source of truth.
A good order for a batch:

1. Triage: group the incoming documents by the category they belong to.
2. For each category group, assign addresses sequentially (`10.01.01`, `10.01.02`, ...),
   create the subfolders, and place the files.
3. Write all passports after placing all files - doing them together keeps the format
   consistent across the batch.
4. Run `das validate` once at the end of the batch, not after every file.
5. Commit the whole batch as one commit with a clear message describing what was filed.

**For a very large batch (tens or hundreds of documents):**

Break it into logical sub-batches (by source, by type, by category) and commit each
sub-batch separately. This keeps the git history readable and makes it easy to find when
a specific document was filed. Each sub-batch should still pass `das validate` before
committing.

---

## When to add a new area

Add a new area when content arrives that does not fit cleanly under any existing area -
not when an existing area is large, and not speculatively.

**Add a new area if:**
- The content is a distinct business function or subject domain that will grow (not a one-off).
- Filing it in an existing area would require stretching that area's label or description
  to cover something it was not designed for.
- The corpus uses gapped numbering and there is a clean slot for it.

**Do not add a new area if:**
- You are just filling the area in case it is needed later. Empty areas with `.gitkeep`
  are fine as placeholders when you are confident the content is coming, but do not create
  areas speculatively.
- The content is a sub-topic of an existing category - add a subcategory instead.
- The area would only ever hold one or two documents - file them at the category level
  and add the area later if it grows.

**Numbering when adding an area:** if the corpus uses gapped numbering (00, 10, 20...),
insert the new area in the natural gap. If it uses sequential numbering and the area
list is dense, append at the end before 99-Archive. Do not renumber existing areas to
make room - that violates the permanence rule.

---

## The promotion path: local to shared

A corpus typically starts local (a single git repo on one machine, no remote) and may
later need to be shared with a team, made into a private org repo, or eventually made
public. Each step has specific actions.

**Local only (a common current state for new corpora):**
- No remote, no sharing concerns, full freedom to reshape while young.
- `das validate` is the only gate before committing.

**Adding a remote (private repo):**
- Push to the org repo as-is. No address changes required - the remote is just a backup
  and sharing mechanism, not a publication event.
- If the corpus has `INT`-tagged documents, confirm the repo is private before pushing.

**Making the corpus accessible to agents or tools:**
- Update `~/Projects/project-registry/` with the corpus entry so agents can resolve it
  by slug. See `docs/project-registry.md`.
- At this point the address space starts to calcify: other agents may begin citing addresses.
  Treat the corpus as Active from here.

**Making part of the corpus public:**
- Audit every file for `clearance: internal` or `INT` tag. Do not publish anything marked
  internal without explicit review.
- For a data/research corpus: the provenance and license fields in every passport must be
  verified before public release. Unknown license = internal only.
- Consider splitting internal-only areas into a separate private corpus rather than
  making the whole thing public with suppressions.

---

## Retiring content: deprecate, never delete

When a document, program, or area is no longer current:

- Set `deprecated: true` on the manifest node. The validator skips deprecated nodes for
  content checks but they remain in the manifest as the permanent record.
- Do not delete the file. If storage is a concern, move it to `99-Archive/` - but keep
  the manifest node pointing to its new location.
- If an entire area is being superseded (e.g. content moved into a nested structure),
  deprecate all its nodes and add a `deprecated_note` to the manifest describing where
  the content moved. See `restructuring-a-corpus.md` for the full reshape procedure.

---

## The ETL ingestion path

When source material arrives in a messy form - PDFs, DOCX files, wiki exports, email
archives, data files dropped in a folder - and needs to become a DAS corpus, the
steps are:

1. **Triage**: decide which corpus layout pattern fits the source material
   (`corpus-layout-patterns.md`). The layout drives the address strategy.
2. **Initialize**: `das init` the corpus with the org, tags, and naming convention for
   this corpus type.
3. **Classify**: group the source material by the areas it belongs to. For document
   corpora this is by topic or function; for data corpora this is by type, source, or
   controller.
4. **Address and file**: for each group, `das add` the category node, create the subfolder,
   place the source file verbatim (never modify the original), and write the passport.
5. **Validate**: `das validate` after each category batch.
6. **Record provenance**: for any sourced material, the passport `source` and `license`
   fields are mandatory before committing. No unsourced files.

This is the manual version of what an automated ingestion/ETL tool could eventually
handle. Until such tooling exists, every ingestion is manual and the steps above are
the process.

**The hardest part of ingestion** is classification, not addressing. Deciding which area
a document belongs in, and whether a new area is needed, requires understanding the
corpus's purpose. The addressing itself is mechanical once classification is done.

---

## Corpus health signals

Signs a corpus needs attention:

| Signal | Likely cause | Action |
|--------|-------------|--------|
| `das validate` reports many "address not in manifest" errors | Files placed without `das add` | Add missing manifest nodes |
| Large number of documents in a single category | Category too broad | Consider splitting into subcategories |
| Areas with only one or two documents | Over-classified at init time | Leave as-is unless causing confusion; do not merge without a reshape |
| Passport fields consistently empty | Filing process skipping passport step | Add passport writing to the batch procedure |
| `INT`-tagged files in a public-accessible repo | Provenance review missed | Audit and move or restrict access |
| No migration record after a reshape | Reshape done informally | Write `das.migration.md` retroactively from git history |
