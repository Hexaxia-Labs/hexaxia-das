# Using DAS as Cool Storage for Agent Memory

As agents do more work, they generate more that is worth remembering. A DAS corpus is a
natural home for an agent's durable long-term memory: addressed, passported, and sitting on
a plain filesystem. DAS plays one specific role in a memory system - the **cool-storage
tier**: the durable system of record that is not resident in the agent's context window, but
is addressable and retrieved on demand.

This document sketches that role. The intelligent recall and consolidation layers that sit on
top are separate systems, out of scope for DAS itself.

---

## Hot, warm, cool

Agent memory spans tiers, from the agent's live context to durable storage:

| Tier | What it is | Where DAS fits |
|------|------------|----------------|
| **Hot** | Working/context memory - the live session, ephemeral | Not DAS |
| **Warm** | An associative index (vector / RAG) for fast recall - rebuildable | Not DAS - built *over* the cool tier |
| **Cool** | The durable record of what the agent has learned | **This is DAS** |

Cool storage is not slow or second-class. It means *durable and retrieved on demand* rather
than *held in context*. You do not load an agent's whole memory into its window; you address
and retrieve the part you need.

---

## Why DAS fits the cool tier

- **Permanent addresses are stable provenance.** "The agent learned X, recorded at `30.01.02`"
  is a durable citation - referenceable from another memory, a log, or a different agent, and
  still valid later. An opaque embedding has no such handle.
- **The passport summary is the recall signal.** The same summary that routes a RAG query
  routes recall: find the address, read the document.
- **It is a plain filesystem.** Memory you can `grep`, `diff`, read offline, and inspect by
  eye - not a record locked inside a service.
- **It is the floor under a rebuildable index.** The warm index is an accelerator built over
  the cool store. Lose or rebuild the index and the memory survives, because the durable trace
  is the addressed document on disk, not the embedding. "Forgetting" is de-indexing (a warm-tier
  operation); the cool-tier record is deprecated, not destroyed.

---

## Consolidation: how memory earns an address

Raw experience is high-rate; durable memory should not be. Only **consolidated** memory - the
generalized distillate of many raw episodes - earns a permanent address. The common shape: raw
records land in an inbox area, and a periodic consolidation pass reviews them, generalizes, and
files the keepers at their permanent addresses. Consolidation is the rate-limiter that turns a
firehose into a cadence the durable store can hold coherently.

The corpus layout for this - memory-type areas, an inbox, temporal-validity passport fields -
is the Agent Memory pattern in
[corpus-layout-patterns.md](corpus-layout-patterns.md#pattern-4-agent-memory).

---

## What DAS does, and what it does not

DAS provides the durable, addressed, provenanced store and nothing more. It does **not** do
similarity search, hot recall, or forgetting - those belong to the warm index and the agent's
runtime. Keeping that boundary clean is the point: a simple, durable floor that the richer
memory and recall systems are built on top of, and that keeps working when they are not
present. Those upper layers are their own systems; DAS is the ground they stand on.

A memory corpus is also just one corpus among others in a workspace - see
[corpus-boundaries.md](corpus-boundaries.md).
