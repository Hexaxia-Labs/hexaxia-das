# Corpus Boundaries and the Workspace Layer

DAS addresses are permanent and unique - but only *within a corpus*. This document explains
where a corpus begins, why the address space resets at every corpus root, and how to use
DAS-style numbering loosely at the level *above* corpora to organize many of them together.
This is the flexibility that lets one filesystem hold many independent corpora of different
organizational types without forcing them into a single rigid address space.

---

## A corpus is an address space, and it has a boundary

A DAS corpus is defined by its root: the directory that contains `das.config.yaml` and
`das.manifest.yaml`. That root is the boundary of one address space. Everything inside it
shares one config, one manifest, one naming convention, and one set of permanent addresses.

The address `02.01.03` is meaningful **inside its corpus** and nowhere else. Two different
corpora can both have an `02.01.03`, and they are unrelated - the same way two different
databases can both have a row with `id = 5`. To reference an address in another corpus you
use a federated reference (`ORG:02.01.03`); see [federation.md](federation.md).

This is the **named-root containment** model: each corpus is self-contained and independent.
Its config, conventions, naming style, and segment width say nothing about how any other
corpus is laid out. See the "Many Corpora, Varying Standards" section of
[philosophy.md](philosophy.md).

---

## Numbering resets at every corpus root

Because the address space is per-corpus, the numbering **resets to `00` at each root**. A new
corpus always starts its areas at `00`, `01`, `02`, regardless of what any sibling corpus
looks like. There is no global address space and no continuation of numbering across corpora.

```
atlas-technologies/         <- corpus root (das.config.yaml here)
  00-Admin/                 <- numbering starts at 00 for THIS corpus
  01-Finance/
  02-Clients/

acme-research/              <- a separate corpus root (its own das.config.yaml)
  00-Datasets/              <- numbering resets to 00 again, independent of atlas
  01-Papers/
```

`acme-research/00-Datasets` and `atlas-technologies/00-Admin` are both `00` and have nothing
to do with each other. The reset is not a limitation - it is what keeps each corpus's address
space small, stable, and human-legible. You never have to coordinate numbers across corpora.

**The practical consequence:** when a body of content grows its own identity, owners, or
access rules, you do not keep extending one giant corpus. You start a new corpus, and its
numbering begins fresh. Deciding when to split versus keep-in-one is covered in
[federation.md](federation.md#when-to-federate-vs-keep-content-in-one-corpus).

---

## The workspace layer: DAS-style numbering above corpora

Here is the flexibility most people miss: **you can use DAS-style numbering at the level
above corpora, too** - not as a strict corpus, but as an organizing convenience.

A *workspace* is a directory that holds multiple independent corpora (and possibly other
things, like code repositories). You can number its top-level entries the same way you number
a corpus's areas, so the workspace reads cleanly and sorts predictably:

```
work/
  00-corpora/               <- holds document corpora (each its own DAS corpus)
    atlas-technologies/      das.config.yaml + manifest  (independent address space)
    acme-research/           das.config.yaml + manifest  (independent address space)
  10-projects/              <- holds code repositories (NOT DAS corpora)
    web-app/
    data-pipeline/
  20-memory/                <- an agent-memory corpus (its own DAS corpus)
    das.config.yaml + manifest
```

The key distinction:

- **`work/` and `00-corpora/` are containers, not corpora.** They have no `das.config.yaml`,
  no manifest, and the `das` tool does not validate them. Their numbering is a loose,
  human-facing organizing scheme - "DAS-style," not DAS-strict.
- **Each leaf that *is* a corpus** (`atlas-technologies/`, `acme-research/`, `20-memory/`)
  carries its own `das.config.yaml` and resets its own address space at `00`.

So the numbering you see at the workspace level (`00-corpora`, `10-projects`, `20-memory`)
is a different, looser application of the same idea - permanent, sortable, glanceable numeric
prefixes - layered *on top of* the strict per-corpus address spaces underneath. The two
levels do not share an address space and do not need to.

---

## Why this is a feature, not a workaround

Keeping the workspace layer loose and the corpus layer strict buys real things:

- **No cross-corpus number coordination.** Each corpus owns its `00`-`99` (or wider) space
  outright. Adding a corpus never renumbers another.
- **Different organizational types coexist.** A document corpus, a code repository, and an
  agent-memory corpus can sit side by side under one numbered workspace, each organized the
  way its content demands. See [corpus-layout-patterns.md](corpus-layout-patterns.md) for the
  patterns a corpus can take (editorial, product/corporate, data/research, agent-memory,
  mixed).
- **Clean split points.** When a corpus should become two (an entity spins out, a public set
  separates from an internal one), the boundary is already a hard line: a new root, a fresh
  address space, no renumbering of the original.
- **The tool stays simple.** `das` operates on one corpus root at a time (via `--path` or the
  current directory). It does not need to understand the workspace above it, because that
  level is convention, not schema.

---

## What the tool manages, and what it does not

| Level | Has `das.config.yaml`? | `das validate` runs here? | Numbering |
|---|---|---|---|
| Workspace (`work/`) | No | No | Loose DAS-style convention |
| Container (`00-corpora/`) | No | No | Loose DAS-style convention |
| Corpus root (`atlas-technologies/`) | Yes | Yes | Strict DAS address space, resets at `00` |
| Inside a corpus (`02.01.03-...`) | (inherits root) | Yes | Strict, permanent, unique within the corpus |

The `das` tool's world begins at a corpus root and ends at that corpus's edges. The workspace
and container levels are yours to organize however reads best - numbering them DAS-style is a
convenience the standard encourages but does not enforce.

---

## Relationship to federation

The workspace layer answers "how do I lay out many corpora on disk." Federation answers "how
does an address in one corpus reference content in another." They are complementary:

- A workspace **organizes** corpora physically; their numbering is independent and never
  joined.
- A federated reference (`ORG:address`) **links** across corpus boundaries when one document
  needs to point at another corpus's content.

Neither merges address spaces. The reset at each corpus root is permanent; federation is how
you reach across it when you must. See [federation.md](federation.md).
