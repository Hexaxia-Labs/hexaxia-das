---
name: synapaxia-memory
description: Use at the start and end of any DAS engineering task or corpus operation to recall prior lessons and record new ones. Wraps synapaxia episodic and procedural memory - search before acting, store after. Triggers when beginning work on the das tool or a DAS corpus, or when the user says remember, recall, "what did we learn", or "have we seen this before".
---

# synapaxia-memory

synapaxia is the DAS agents' memory layer. It stores **episodes** (what happened on a
specific task and what worked) and **procedures** (reusable how-tos). It does NOT store
document content - corpus documents live on the filesystem under DAS addresses.

Use this skill as bookends around real work: recall first, store after.

## Before acting - recall

1. Search procedures for a reusable approach:
   - `mcp__synapaxia__search_procedures` with a short description of the task
     (e.g. "navigate a DAS corpus for an enumeration question").
2. Search episodes for corpus- or feature-specific lessons:
   - `mcp__synapaxia__search_episodes` with the corpus name or feature area
     (e.g. "Hexaxia-Technologies Q4 enumeration routing").
3. If a relevant procedure or episode is found, follow it. If it conflicts with the
   current research docs or spec, prefer the docs and note the conflict in your next
   stored episode.

## After acting - store

1. If you discovered a reusable approach, store it as a procedure:
   - `mcp__synapaxia__store_procedure` - name it, describe when to use it and the steps.
2. Always store an episode capturing the concrete outcome:
   - `mcp__synapaxia__store_episode` - include the corpus or feature, what you tried,
     what worked, and any dead ends. Be specific: "corpus X, Q4-class enumeration needs
     manifest-first; RAG misroutes 'active projects' to social posts."

## Scope rules

- Memory only. Never put document bodies, secrets, or full file contents into synapaxia.
- Keep entries short and queryable - name the corpus, the question class, the outcome.
- Operator stores corpus-operation lessons; engineer stores design decisions and rationale.
