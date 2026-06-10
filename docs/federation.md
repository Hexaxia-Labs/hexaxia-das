# Federation: Multi-Corpus Addressing

Federation is how two or more DAS corpora reference each other's addresses unambiguously.
A federated reference includes the corpus identifier so that any reader - human or agent -
can resolve it to the right corpus without guessing.

This document describes the federated address format, when to federate vs. keep content
in a single corpus, and how agents resolve cross-corpus references.

---

## The federated address format

A standalone DAS address (`10.02.07`) is unambiguous within a single corpus but
meaningless outside it. The federated format adds a corpus identifier:

```
{ORG}:{address}
```

Examples:
```
ATL:10.02.07
ATL:02.01.03
FND:10.01.01
```

The org code comes from the corpus's `das.config.yaml` `org` field. When a corpus uses an
org code, federated references to any of its content use that code as the namespace prefix.

For corpora without an org code (local or personal corpora), the corpus slug from
`das.config.yaml` `corpus` serves as the namespace:

```
atlas-content:04.01.02
foundry:10.02.07
```

**The format is advisory, not enforced by the current tooling.** `das validate` does not
check cross-corpus references. Federation is a documentation and naming convention at this
stage - the tooling support is deferred. But writing federated references correctly now
means they will be resolvable when tooling support lands.

---

## When to use federated references

A federated reference is appropriate any time a document in one corpus points to content
in another corpus:

- A passport `see_also` field pointing to a related document in a different corpus:
  ```yaml
  see_also: ["ATL:02.01.03", "FND:30.01.01"]
  ```
- An agent memory record referencing an artifact in a data corpus:
  ```
  Baseline measurement for the reference dataset is in FND:10.01.01
  ```
- A design document cross-referencing a spec section in another corpus:
  ```
  See RLY:20.03.01 for the API contract this implements.
  ```
- A project registry entry mapping a corpus slug to its filesystem path

In all these cases, the federated form `ORG:address` makes the reference self-contained:
a reader or agent that encounters it knows both what to look for and where to look for it.

---

## When to federate vs. keep content in one corpus

The decision to split content across multiple corpora (and therefore require federation) or
keep it in one corpus (and use simple addresses) has real tradeoffs. See also
`docs/corpus-layout-patterns.md` on the mixed pattern.

**Keep in one corpus when:**
- The content is tightly coupled - one layer exists to validate or describe the other
- Cross-references are frequent and the corpus is actively maintained
- The corpus is local and not yet shared with other agents or teams
- The patterns share the same tag vocabulary and naming convention
- The corpus is young enough that a single manifest is not unwieldy (under ~500 nodes)

**Federate (split into separate corpora) when:**
- The content has independent owners or access controls
- One layer is public and the other is internal
- The access patterns diverge significantly (one corpus is read frequently, the other rarely)
- The naming conventions are genuinely incompatible between layers
- The corpus is large enough that a single manifest becomes slow to load or hard to maintain
- Different agents need to operate in different sub-collections with independent trust boundaries

The named-root containment model means each corpus is an independent trust boundary. An
agent assigned to operate in `Foundry` does not automatically have access to `Relay` - the
roots are separate and the assignment is explicit. If you need an agent to operate across
both, it must be given both roots, and it must use federated references to unambiguously
address content in each.

---

## How agents resolve cross-corpus references

The `~/Projects/project-registry/` directory is the federation gateway. It maps corpus slugs
(and org codes) to filesystem paths. See `docs/project-registry.md` for the format.

When an agent encounters a federated reference like `ATL:10.02.07`:

1. Extract the org code or corpus slug (`ATL`)
2. Query the project registry to resolve it to a corpus root path
3. Open `das.manifest.yaml` in that corpus root
4. Look up address `10.02.07` in that manifest
5. Navigate to the resolved path

This is "step 0" from the agent guide, applied to a secondary corpus rather than the primary
one. Each corpus encountered through federation is opened and read independently.

**Current limitation:** the project registry is a local lookup table. It works within a
single workstation or shared filesystem. Cross-machine or cross-organization federation would
require a shared registry service - this is a deferred capability.

---

## Federation vs. the project registry

The project registry (`~/Projects/project-registry/`) and federation are related but distinct:

- The **project registry** is how an agent resolves a corpus slug to a filesystem path.
  It is the gateway to any corpus, whether referenced by a federated address or not.
  It is consulted at agent startup to identify the primary corpus root.

- **Federation** is how addresses in one corpus reference content in another corpus.
  It is consulted when a document or agent encounters a cross-corpus reference like `ATL:10.02.07`.

Both use the org code or corpus slug as the lookup key. The project registry provides the
mapping from that key to the filesystem path.

---

## Writing federated references correctly

When writing a cross-corpus reference, use the federated format even if it feels redundant
in context. The context changes; the reference should be self-describing.

**In a passport `see_also`:**
```yaml
see_also:
  - "ATL:02.01.03"    # engagement contracts in the main Atlas corpus
  - "FND:10.01.01"    # related dataset in Foundry
```

**In an agent hint:**
```yaml
agent_hint: "Product spec. API contract at RLY:20.03.01. See FND:30.01.01 for the
             safety case that this feature must satisfy."
```

**In a document body:**
```
The validation methodology is documented at FND:10.02.01-SYNTH-note-conventions.md.
```

Using the full federated form `ORG:address` is always preferred over "see the Foundry corpus"
or "see the Relay corpus" - it gives the agent a resolvable address rather than a corpus name
it has to look up.

---

## Org code vs federation prefix

A corpus's `org` code (e.g. `ATL`) is its namespace identifier, declared once in
`das.config.yaml`. It serves as the federation prefix: `ATL:02.01.03` resolves an address
across corpora to the Atlas corpus. The org code is a corpus-level identifier, not a
filename component - per-file scoping is done with `tags` (see the main spec). A corpus
without an org code falls back to its corpus slug as the federation namespace.

An address without a federation prefix is always a local address in the current corpus.

---

## Versioning across federated corpora

DAS addresses are permanent within a corpus but corpora are independent. If a corpus is
restructured (its areas are reshaped), the old addresses are deprecated and new ones are
added. Any cross-corpus references to the deprecated addresses will need to be updated.

The `das.migration.md` file at the corpus root records reshapes and address remapping.
See `docs/das-migration-convention.md`. When an agent resolves a federated reference and
finds a `deprecated: true` manifest node, it should check the `deprecated_note` or the
migration record to find the replacement address.

---

*See also: `docs/corpus-boundaries.md` (per-corpus address reset and the workspace layer),
`docs/project-registry.md`, `docs/agent-guide.md`, `docs/das-migration-convention.md`,
`docs/spec.md` section 10.3 (federation, deferred)*
