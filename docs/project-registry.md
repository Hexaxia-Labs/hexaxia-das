# The Project Registry

How an agent finds which corpus to open in the first place.

DAS makes navigation *inside* a corpus fast - permanent addresses, a manifest, a filename
jump-table. But before any of that helps, an agent has to answer a more basic question: where
on disk does this corpus live? With many projects spread across `~/Projects/`, hunting with
`find`, `ls`, or `grep` is slow, fragile, and burns user attention. The project registry
removes that step. It is the first source of truth - "step 0" above all in-corpus navigation -
and it is what lets an agent work across many corpora without being told a path every time.

The registry described here is a pattern, illustrated with the layout and tooling of a real,
in-use implementation - adapt the paths and script to your own environment. This page describes
the pattern and its relationship to DAS. The registry is the authoritative source for its own schema and
usage; this page summarizes and links to it rather than restating it.

> **Source of truth:** `~/Projects/project-registry/` (its own repository, local-only). The
> `das` CLI does not manage or read the registry - they are complementary tools that the DAS
> agent relies on together.

---

## The registry at a glance

- **Location:** `~/Projects/project-registry/`
- **The data:** `registry.yaml` - a single `projects:` list, one entry per project, spanning
  every division or team that owns projects.
- **The interface:** `lookup.sh` - a self-contained Bash + embedded Python script with no
  external dependencies. It resolves a project deterministically by slug.
- **Scope:** a general project index, not DAS-specific. It tracks websites, agents,
  libraries, client engagements, and document corpora alike.
- **Local-only:** never pushed to GitHub - it contains local filesystem paths and client names.

Each entry carries a small set of fields. A short summary follows; the registry's own
`docs/schema.md` and `docs/usage.md` are authoritative.

| Field | Required | What it holds |
|---|---|---|
| `slug` | Yes | Unique lookup key - lowercase, hyphenated |
| `name` | Yes | Human-readable display name |
| `division` | Yes | Owning division or team |
| `type` | Yes | What kind of thing it is (product, website, agent, docs, ...) |
| `status` | Yes | `active`, `paused`, or `archived` |
| `path` | Yes | Absolute local path to the project root (this is the DAS link) |
| `branch` | No | Working branch when it is not `main` |
| `stack` | No | Technology stack |
| `url` | No | Live site or local service URL |
| `notes` | No | One or two sentences of operational context |

Do not reproduce the full schema here - when in doubt, read the registry's own docs.

---

## Finding a corpus: lookup.sh

Agents resolve a project by slug. No filesystem search, no embeddings, no guessing.

```bash
# Full project card
~/Projects/project-registry/lookup.sh atlas-technologies

# Just the path (for scripts and cd)
~/Projects/project-registry/lookup.sh --path atlas-technologies

# All active projects
~/Projects/project-registry/lookup.sh --list
```

`--path` returns the bare absolute path with `~` expanded, ideal for piping into a `cd` or a
tool invocation. The script resolves `registry.yaml` relative to its own location, so it works
from any working directory. The lookup is deterministic and instant - exactly the property you
want for the one step that has to happen before navigation can begin.

---

## The DAS relationship

A DAS corpus is just a registry entry whose `path` points at the corpus root. There is no
special corpus type and no separate index - the registry treats a corpus exactly like any other
project. The link between the two systems is that one `path` field.

The registry's own schema docs use a real DAS corpus as a path example:

```yaml
  - slug: acme
    name: Acme Corp (Client)
    division: services
    type: client-engagement
    status: active
    path: ~/work/00-corpora/example-corp/02-Clients/02.01-ACME
```

That `path` is a DAS corpus root (or a node within one). Once an agent has resolved it, every
DAS mechanism - the manifest, the address space, the filename jump-table - takes over. The
registry is step 0; DAS navigation is steps 1 and onward.

---

## Agent workflow

The full path from a task to an answer puts `lookup.sh` first, then layers DAS navigation
inside the resolved corpus. RAG is an optional accelerator, not a requirement (see the next
section).

```
  task: "what's the status of the ACME NetBird deployment?"
                          |
                          v
            +-------------------------------+
            |  STEP 0: registry             |
            |  lookup.sh <slug>             |   deterministic, no embeddings
            |  -> corpus root path          |
            +-------------------------------+
                          |
                          v   (now inside the corpus)
            +-------------------------------+
            |  STEP 1: in-corpus DAS nav    |
            |                               |
            |  RAG pre-query  (optional     |
            |    accelerator, -33% turns)   |
            |        |                      |
            |        v                      |
            |  manifest  (address map,      |
            |    best for enumeration)      |
            |        |                      |
            |        v                      |
            |  filesystem jump-table        |
            |    (numeric prefixes in       |
            |     ls output, always there)  |
            +-------------------------------+
                          |
                          v
            +-------------------------------+
            |  STEP 2: answer from the      |
            |  content of the file you      |
            |  actually read - never from   |
            |  a passport summary alone     |
            +-------------------------------+
```

Each rung of step 1 degrades gracefully to the one below it: a RAG pre-query narrows to an
address, the manifest resolves the address to a path, and the numeric jump-table is the floor
that always works when neither is available. The registry supplies the corpus root that this
in-corpus navigation assumes you already have.

---

## DAS without RAG

The deterministic spine of this whole workflow needs zero embeddings:

```
lookup.sh (no embeddings)  +  DAS addressing (manifest / filename jump-table)
        =  correct navigation with no RAG at all
```

The navigation benchmark shows the no-RAG layers stand on their own:

- **Filesystem jump-table** (numeric prefixes in `ls` output) is roughly neutral versus the
  messy real-world baseline - the addresses cost nothing and earn their keep by letting agents
  discard irrelevant areas at a glance.
- **das-manifest** routing comes in at **-13%** turns versus baseline, and is the *best*
  pattern for sub-tree enumeration questions.
- **rag-nav-mxbai** reaches **-33%**, the overall winner - but it is an *accelerator on top of*
  DAS addressing, not a precondition for navigation. When Ollama is down or a corpus has not
  been embedded, the manifest and jump-table still resolve the answer.

`lookup.sh` is itself part of this deterministic spine: it has no embedding dependency. Note
that the registry's README and docs can also be embedded in an agent's RAG index, so an agent
can discover registry content via fuzzy semantic search ("where is the billing dashboard?"). That is a
convenience for discovery. For precise path resolution, `lookup.sh` is the preferred,
deterministic, authoritative method - prefer the direct call over RAG for "give me the path to
X" questions.

---

## Relationship to the manifest and federation

The registry, the manifest, and the address each answer a different question. They nest:

| Scope | Question it answers | Artifact |
|---|---|---|
| Registry | Which project / corpus? | `registry.yaml` + `lookup.sh` |
| Manifest | Which address within the corpus? | `das.manifest.yaml` (spec [section 6](spec.md)) |
| Address / filename | Which exact file? | the node name on disk |

The registry sits one level *above* the manifest. The manifest (spec section 6) is the corpus
map - it resolves a question to an address once you are inside a corpus. The registry resolves
which corpus to enter in the first place.

This also dovetails with **federation** (spec [section 10.3](spec.md)), the deferred future
work on unified addressing across multiple DAS corpora. Federation would scope addresses to
their origin corpus via an org-prefix scheme. The two are complementary: the registry already
maps a slug to a corpus root today, which is exactly the slug-to-path resolution table a
federated addressing layer would need. The registry could become federation's resolver without
changing what it is.

---

## Scope and status

The project registry is a **real, in-use external project** with its own repository at
`~/Projects/project-registry/`, maintained manually and kept local-only. It is not a deferred
or hypothetical DAS feature.

- The `das` CLI does **not** read, write, or depend on the registry. No `das` code touches it.
- The registry does **not** depend on DAS. A DAS corpus is just one kind of entry it can hold.
- They meet at exactly one point: a registry entry's `path` field, which may point at a DAS
  corpus root.

Treat the registry as an existing ecosystem tool that the DAS agent relies on for step 0, and
treat `~/Projects/project-registry/` as the source of truth for its schema, usage, and current
contents.
