# The Philosophy of Hexaxia DAS

## Where This Came From

Johnny.Decimal is one of the most useful personal organization systems ever designed. Its core
insight - that a small, fixed set of permanent numbers is more useful than an endlessly refined
folder hierarchy - is genuinely correct. For an individual managing their own files, JD's
two-level limit is not a constraint. It is a feature. It forces the kind of discipline that
makes a system actually usable.

Hexaxia DAS does not exist because JD is wrong. It exists because JD was designed for a single person,
and organizations are not single people.

When you scale a JD corpus across a company with dozens of clients, multiple service lines,
years of history, and eventually AI agents navigating alongside humans - you hit the ceiling.
Hexaxia DAS is what you build when you've hit that ceiling and you want to keep the one principle that
actually matters: **numbers are permanent**.

---

## The Core Analogy: DNS for Documents

The clearest way to understand Hexaxia DAS is through the DNS analogy.

Every device on a network has an **IP address** - a stable, machine-parseable numeric identifier
that never changes and is globally unambiguous. It also has a **hostname** - a human-readable
name that can be updated, pointed at a different address, or changed entirely without breaking
anything that references the underlying IP.

Hexaxia DAS gives every folder and file the same two-part identity:

- The **DAS address** (`02.01.03`) is the IP address. Permanent. Machine-parseable.
  An agent strips everything after the first hyphen and has a precise coordinate.
- The **human label** (`Active-Projects`) is the hostname. Readable. Can change when
  the content changes. Never changes the address beneath it.

These two components are fused in the filesystem: `02.01.03-Active-Projects/`. They travel
together. An agent reads the prefix. A human reads the suffix. Neither gets in the other's way.

This is not a filing convention. It is an addressing system with a human display layer on top.

---

## Why JD Breaks at Organizational Scale

Johnny.Decimal's two-level limit (10 areas of 10 categories each) is intentional. The
philosophy is: if you need more than 100 buckets, you have too much stuff and need to think
harder about organization. For personal use, this is sound advice.

For organizations, it fails in four specific ways:

**1. The space is too small.**
A company with 10 active clients, 5 service lines, 4 internal departments, and 3 years of
history cannot fit into 100 categories. Not without either merging things that should be
separate (too few categories) or creating artificial top-level splits that violate the
"one home per thing" rule (too many areas). The math simply does not work.

**2. There is no machine-readable schema.**
Standard JD is convention-only. There is no file that describes the address space. An AI
agent navigating a JD corpus has no choice but to traverse every folder in the tree to
understand what exists and where. At 10,000 documents this is slow. At 100,000 it is
impractical.

**3. Filenames do not carry their location.**
A file named `Business Plan 2024.docx` contains no information about where it belongs.
An agent that finds this file as an email attachment cannot determine its home in the corpus
without a search. Hexaxia DAS files carry their address: `04.02.01-HXT-business-plan-240101.docx` is
unambiguous. The location is in the name.

**4. There is no configuration artifact.**
Different people in a JD corpus make different naming choices. There is no canonical way to
record whether dates go before or after the descriptor, whether org codes exist, or what the
context identifier means. Every corpus is subtly different. This is fine when one person owns
the corpus. It is a problem when ten people contribute to it, and a serious problem when an
agent is expected to navigate it.

Hexaxia DAS solves all four. The depth limit is lifted. The manifest provides a machine-readable map.
Filenames carry their address. The config file locks the naming schema at initialization.

---

## The One Principle Worth Keeping

JD and Hexaxia DAS agree on exactly one thing: **addresses are permanent**.

Once a DAS address is assigned to a node, it never changes. It never gets renumbered. If the
client at `02.01` changes their name, the label changes - but the address `02.01` stays. If the
engagement ends, the address is retired by setting `deprecated: true` in the manifest - it is
never recycled, never reused, never given to a different client.

This permanence is what makes the address safe to reference from outside the corpus. A database
record, a contract, an agent's long-term memory, a document passport - any of these can record
`02.01` and know with certainty that it will always resolve to the same entity, even years later.

Without permanence, an address is just a shortcut. With permanence, it becomes a stable
identifier that external systems can trust.

---

## Schema-First Design

The `das.config.yaml` file is the corpus constitution. It declares - once, at initialization -
what the naming schema is for every file that will ever live in this corpus:

- Does this corpus include an org code in filenames?
- What does the context identifier represent - a client, a project, a department?
- Are dates included in filenames, and in what format?

These decisions are **immutable after initialization**. This is not an accident or an oversight.
It is a deliberate design choice based on a simple observation: every filename in the corpus
depends on these decisions being stable. If you change the schema, every existing filename is
now wrong relative to the new schema. There is no safe way to change the config without
migrating every file - which is why Hexaxia DAS treats a config change as a breaking migration
requiring documentation and a full rename pass.

The immutability of the schema is the mechanism that makes a DAS corpus trustworthy over time.
You can add files. You can deepen the hierarchy. You can update labels. You cannot change what
the names mean.

---

## The Manifest as the Corpus Map

The `das.manifest.yaml` file is the corpus map. It lists every address that has ever existed,
what it contains, how it relates to its parent, and - optionally - routing hints for agents.

An AI agent that loads the manifest once can answer "where does X live?" for the entire corpus
without traversing a single folder. It knows that `02` is Clients, that `02.01` is the ULS
engagement, that `02.01.01` is Contracts. It can navigate the address space the way a network
device navigates a routing table - by consulting a pre-built map, not by exploring the terrain.

The `agent_hint` field is the explicit acknowledgment that agents are first-class navigators in
a DAS corpus. When you write a hint like `"Primary MSP client. Contracts in 02.01.01, active
projects in 02.01.03."`, you are not writing documentation for yourself. You are writing
routing context for an agent that will use this corpus long after you have forgotten what you
put where.

---

## Depth as Something You Earn

Hexaxia DAS imposes no hard depth limit. In theory, you can go as many levels deep as the content
requires. In practice, depth should be **earned**, not assumed.

The guidance is:
- **4 levels** covers the needs of most organizations
- **5 levels** is a yellow flag - ask whether the level above is too broad
- **6 levels** is a red flag - something upstream needs restructuring

This is not an arbitrary aesthetic preference. It reflects a real relationship between depth
and navigation cost. Every level you add requires anyone navigating the corpus - human or agent
- to hold one more level of context. Deep hierarchies are not wrong, but they are expensive.
Before adding a level, the question to ask is: "could I achieve the same organization with
better labels at the current depth?"

When the answer is no - when the current node genuinely has too many children with too much
natural variation between them - then a new level is warranted. Not before.

---

## What Hexaxia DAS Is Not

**Hexaxia DAS is not a replacement for Johnny.Decimal.**
For personal use, JD is the right tool. Hexaxia DAS's additional complexity - the config file, the
manifest, the naming convention - is overhead that a single person does not need and should
not carry. Hexaxia DAS is for when JD's constraints are the problem, not the solution.

**Hexaxia DAS is not a document management system.**
Hexaxia DAS does not manage access control, version history, workflow routing, or document lifecycle.
It is an addressing and organization standard. It tells you where things live and gives those
locations stable names. What you do with the documents once located is outside its scope.

**Hexaxia DAS is not a search replacement.**
The manifest enables fast structural navigation, but full-text search across document contents
is a separate concern. DAS addresses are designed to be stable identifiers, not search indices.

**Hexaxia DAS is not finished.**
Version 0.1.0 is a working proof of concept. Agent navigation, document passport integration,
and multi-corpus federation are designed but deferred. The standard is intentionally minimal
at v0.1.0 - stable enough to build on, open enough to extend.

---

## The Divergence from JD: A Summary

| Dimension | Johnny.Decimal | Hexaxia DAS |
|---|---|---|
| Intended scope | Personal file organization | Organizational document corpora |
| Depth limit | 2 levels (by design) | Unlimited, guided by soft caps |
| Address range | 10 areas of 10 categories | 00-99 at every level |
| Filename role | Human navigation only | Machine-parseable coordinate |
| Schema artifact | None - convention only | `das.config.yaml` + `das.manifest.yaml` |
| Naming convention | Informal, per-user | Formally defined, corpus-configured, immutable |
| Agent navigation | No | Yes - manifest is the corpus map |
| Multi-entity | No | Designed for (deferred to v0.2+) |
| Immutability scope | Numbers permanent | Numbers + full naming schema permanent |

The divergence is not a criticism of JD. It is an acknowledgment that organizational scale
introduces requirements that JD explicitly chose not to address. Hexaxia DAS carries forward the one
principle that works at any scale - permanence - and builds a complete standard around it.

---

## Why This Format Is Being Used

Hexaxia DAS was designed to solve a specific, real problem: Hexaxia Technologies manages a growing
document corpus spanning multiple clients, service lines, and years. Standard JD ran out of
room. No existing alternative provided both human navigability and machine-readable structure.

The deeper motivation is the convergence of two trends:

**Document corpora are growing faster than human navigation can scale.**
A company that adds 50 documents a month accumulates thousands of files over a few years. At
that scale, "I'll remember where I put it" stops working. The corpus needs structure that is
systematically navigable, not just intuitively organized.

**AI agents are becoming active participants in document work.**
Agents that draft, summarize, cross-reference, and retrieve documents need to navigate the
same corpus that humans do. But agents navigate differently. They do not browse - they query.
They do not remember locations - they look up coordinates. An address system that is also a
machine-readable map is not a nice-to-have for agents. It is the prerequisite for them being
useful at all.

Hexaxia DAS was built to serve both audiences at once: humans who need to find and name things, and
agents that need to navigate and reason about where things are. The address is the bridge
between them.

---

*Hexaxia DAS v0.2.0 | Hexaxia Technologies | 2026-05-27*
