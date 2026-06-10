# Agent Guide: Navigating a DAS Corpus

This guide is written for AI agents that operate within a DAS corpus. It describes the
navigation protocol, the data available to support routing decisions, and the patterns
for performing common operations.

A human reading this guide should understand what a correctly-configured agent can and
cannot do in a DAS corpus, and what to put in the corpus to make agents more effective.

---

## The navigation contract

A DAS corpus makes two guarantees to any agent that enters it:

1. **The manifest is the map.** Every addressed location in the corpus has an entry in
   `das.manifest.yaml`. An agent that loads the manifest once can answer "where does X
   live?" for the entire address space without traversing a single folder.

2. **Addresses are permanent.** A DAS address will never be reassigned, renumbered, or
   recycled. If an agent stores `02.01.03` as a reference to a specific document set, that
   reference will be valid indefinitely. Deprecated addresses remain in the manifest with
   a `deprecated: true` flag; they do not disappear.

These two guarantees are the foundation of the navigation protocol below.

---

## Step 0: Identify your corpus root

Before navigating, an agent must identify which corpus root to operate in.

The `~/Projects/project-registry/` directory (see `docs/project-registry.md`) maps corpus
slugs to filesystem paths. A correctly-configured agent resolves the target corpus via this
registry before opening any DAS files. One corpus root is the agent's entire universe for
the duration of its task - it does not browse across roots unless explicitly federating.

The corpus root contains:
- `das.config.yaml` - the corpus schema and tag vocabulary
- `das.manifest.yaml` - the full address map
- Addressed folders and files organized by the naming convention

---

## Step 1: Load config and manifest

On entry to any DAS task, read both YAML files into working memory.

**`das.config.yaml`** tells you:
- `corpus` - the slug for this corpus (use in log messages and federation references)
- `org` - the corpus's namespace identifier (used in federation references like `ATL:address`, not in filenames)
- `tags` - the controlled vocabulary; only these codes are valid in filenames
- `naming` - the filename convention for this corpus (style, draft/published patterns)

**`das.manifest.yaml`** tells you:
- Every addressed node: `label`, `description`, `type`, `parent`
- Optional `agent_hint` fields - routing guidance written specifically for agents
- `deprecated: true` nodes - retired addresses to route around

You now have a complete map of the corpus. Do not traverse the filesystem to understand
structure - consult the manifest. Filesystem traversal is for locating specific files within
a known address, not for discovering the address space.

---

## Step 2: Route to the right address

Given a task or query, identify the correct address before touching any file.

**The routing steps:**

1. Read all `agent_hint` fields from the manifest. These are explicit routing cues written
   for agents - they describe what a node contains and where related material lives.
   ```yaml
   agent_hint: "Primary MSP client. Contracts at 02.01.01, active projects at 02.01.03."
   ```

2. Search `description` fields for keyword matches. The manifest `description` is a
   human-written summary of what the node contains.

3. Use `das find <keyword>` (or search the manifest directly) when the hint and description
   are not conclusive.

4. Confirm the address is not deprecated before routing to it. A `deprecated: true` node
   may still be the right starting point to understand history, but do not create new content
   under it.

**Address anatomy for routing:**

```
10.02.07
^^ ^^  ^^
|  |   +-- subcategory / document: individual artifact
|  +------ category: the grouping within this area
+--------- area: the top-level domain
```

From any address you can derive the parent: strip the last `.NN` segment.
From the parent you can enumerate siblings: find all manifest nodes sharing the same parent.

---

## Step 3: Navigate to a specific file

Once you have the target address, navigate the filesystem using the DAS folder structure.

Folders are named `{address}-{Title-Cased-Label}/`. The address is always the first token
before the first hyphen. To find all content at address `10.02.07`:

```bash
find . -maxdepth 4 -type d -name '10.02.07-*'
```

To find a file by tag (for documents tagged with a specific context code):

```bash
find . -name '*-ACME-*'
```

Tag-based search is often the fastest way to enumerate all files belonging to a specific
entity across the corpus without traversing every folder.

To navigate to a specific document type at an address:

```bash
find . -name '10.02.07-*-log-*'
find . -name '10.02.07-*-reference-*'
```

---

## Step 4: Read the passport before acting

Before creating, modifying, or reporting on a document, read its passport if one exists.

A passport is embedded in the document's frontmatter (or, for binary artifacts in
data/research corpora, carried in a `.md` sidecar at the same address). The core fields:

- `status` - lifecycle state. A `deprecated` or `archived` document is superseded; do not
  treat it as current. Check the manifest node's `deprecated` flag as well.
- `type` - the authoritative document type (the filename slug is only a navigation echo)
- `summary` - what the document contains; read it before opening a long document
- `tags` - the entities/scopes this document belongs to

Pattern-specific sidecar fields (data/research corpora - see `corpus-layout-patterns.md`):
`source` and `license` (provenance required before using or redistributing an artifact),
`verified_good` (whether the artifact is confirmed correct), `clearance` (`public` or
`internal` - do not surface `internal` content in public-facing outputs without explicit
instruction).

Routing hints (`agent_hint`) live on **manifest nodes**, not in passports.

See `docs/passports.md` for the full field reference.

---

## Step 5: Create content correctly

When creating a new file, use `das new` to generate a correctly-named file at the target address:

```bash
das new 02.01.01 contract msa --tag NSL
```

This resolves the folder, applies the corpus naming convention, validates the type slug and
tag against the config, and writes a passport stub.

If creating files programmatically:
1. Confirm the target address exists in the manifest. If not, `das add` it first.
2. Confirm the target folder exists. If not, create `{address}-{Label}/`.
3. Apply the naming convention from `das.config.yaml` `naming` block. The `style` field
   tells you which pattern to use: `das-address`, `slug-date`, or `custom`.
4. If the corpus uses sidecar passports (data/research pattern), write the passport stub
   alongside the artifact. Do not leave it empty - at minimum, fill `source` and `clearance`.
5. Run `das validate` after filing. Do not commit until validation is clean.

---

## Common operations

**"Find all documents belonging to client NSL"**
```bash
find . -name '*-NSL-*'
```
Then read each passport for `clearance` before surfacing results.

**"Find where the contracts for this client live"**
1. `das find "client name"` or search manifest `description` fields
2. Look for an `agent_hint` on the matched node pointing to the contracts subcategory
3. Navigate to that address

**"What is at address 10.02.07?"**
```bash
das ls 10.02.07          # manifest entry: label, description, agent_hint
find . -name '10.02.07-*'  # all files at this address
```

**"Is there a passport for this file?"**
Look for a `.md` file at the same address in the same folder:
```bash
find . -name '10.02.07-*.md'
```

**"What is deprecated in this corpus?"**
```bash
grep -r "deprecated: true" das.manifest.yaml
```

**"Enumerate all areas and their agent hints"**
Read all top-level manifest entries (depth = one segment). The `agent_hint` on each area
node is the highest-level routing guidance available.

---

## What agents should not do

**Do not traverse the filesystem to understand corpus structure.** The manifest is the map.
Walking the folder tree is slow, misses deprecated content, and will include untracked files
that may not be valid DAS content.

**Do not create content without a manifest entry.** Every file in a DAS corpus has a manifest
node. A file without a manifest node will fail `das validate`.

**Do not infer the naming convention from existing files.** Read `das.config.yaml` instead.
The naming convention is declared, not guessed.

**Do not surface `internal` content externally.** Check the `clearance` field in the passport
before including anything in an external-facing output.

**Do not reuse or renumber addresses.** The permanence rule is absolute. If an address is
deprecated, the next available address is the one to use.

**Do not guess the next available address.** Read the manifest to find the highest existing
address at the target level, then increment. `das add` handles this; if adding manually,
verify against the manifest first.

---

## What makes a corpus agent-friendly

The `agent_hint` field on manifest nodes is the highest-leverage investment for agent
performance. An area node with a hint like `"Primary MSP client. Contracts at 02.01.01,
active projects at 02.01.03."` lets an agent route to the right subcategory in one manifest
read. A hint-free area node requires the agent to read every descendant's description.

The benchmark findings show that:
- The rag-nav pattern (manifest load + RAG retrieval) is the best general navigation strategy
- Tag-based discovery with `find . -name '*-TAG-*'` is the best pattern for entity-scoped search
- Passport quality is the highest-leverage improvement lever for retrieval accuracy

When writing `agent_hint` values, write them as routing instructions: "what addresses does
an agent need to know to work in this node's subtree?" Not a description of contents - the
description field covers that. A jump table of addresses.

---

*See also: `docs/passports.md`, `docs/project-registry.md`, `docs/federation.md`,
`docs/spec.md` sections 4-5*
