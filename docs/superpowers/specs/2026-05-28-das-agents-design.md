# DAS Agents Design

**Date:** 2026-05-28
**Author:** Aaron Lamb (with Claude)
**Status:** Approved design - pending implementation plan

Two project-local Claude Code agents for the Hexaxia DAS project, plus a focused
skill library. One agent builds the `das` tool (AI/ML engineering); the other
operates real DAS corpora (intelligent archivist). Both use synapaxia purely as
an operational memory layer.

---

## Goals

1. A **dev specialist** that designs, researches, and implements the `das` tool's
   intelligent-retrieval features, grounded in the closed benchmark findings rather
   than relitigating them.
2. An **operator specialist** that ingests, addresses, retrieves from, and audits
   real DAS corpora, embodying the validated `rag-nav` navigation pattern.
3. Clean separation: each agent is a thin router; capability lives in small,
   independently testable skills.
4. No new Claude Code plugin and no new repo dependencies. synapaxia (already
   wired) is the only external service, used as agent memory only.

## Non-Goals

- Re-running or extending the navigation benchmark by default. The benchmark is a
  closed study (`docs/research/benchmark-design-260528.md`); its findings are
  settled. The engineer *may* run the external harness to validate a new ML change,
  but routine work builds on the findings.
- Storing corpus document content in synapaxia. Documents live in DAS corpora on
  the filesystem; synapaxia holds only the agents' episodes and procedures.
- Building in-repo RAG infrastructure (embedding/vector store) now. The operator
  degrades gracefully to manifest-first / filesystem navigation when Ollama and
  ChromaDB are absent.

---

## Architecture

Everything is project-local under `hexaxia-das/.claude/`, version-controlled with
the repo and available to anyone who clones it.

```
.claude/
  agents/
    das-engineer.md            # Agent A - AI/ML dev for the das tool
    das-operator.md            # Agent B - operates real DAS corpora
  skills/
    das-feature-tdd/           # engineer: the project's TDD + impl/test/doc/changelog loop
    retrieval-design/          # engineer: design retrieval features from benchmark findings
    embedding-eval/            # engineer: validate an ML/retrieval change vs the nav-test harness
    rag-nav-retrieval/         # operator: the validated rag-nav-mxbai pattern + manifest fallback
    corpus-ingest/             # operator: das add -> type -> passport -> selective tags -> manifest
    writing-passport-summaries/ # operator: wraps the existing high-leverage guide
    corpus-audit/              # operator: das validate + passport/tag hygiene + missing indexes
    synapaxia-memory/          # shared: record/recall episodes + procedures
```

Two thin agents, eight small skills. Agents route to skills; they do not carry
domain knowledge inline beyond what is needed to decide which skill applies.

---

## Agent A - `das-engineer`

**Role:** Full-spectrum AI/ML engineer for the `das` tool. Researches and designs
retrieval approaches, writes specs, and implements them with TDD plus the full
build/test loop.

**System prompt encodes the settled findings** so the agent builds on them:
- Numeric address prefixes earn their keep (descriptive naming is +30% worse).
- `mxbai-embed-large` routes 7/8 vs nomic 3/8 - embedding model is the highest-leverage RAG variable.
- The passport `summary` field is the entire RAG signal.
- Folder address prefixes are not required; the filename carries the jump-table signal.
- Tags help targeted enumeration, cost broad navigation - apply selectively.

**It also carries the 7 open questions** (larger corpora, mixed adoption, passport+RAG
for discovery, better summaries, manifest+RAG hybrid, longer runs, cost measurement)
so it knows the frontier.

**Tools:** Read, Edit, Write, Bash (`.venv/bin/pytest`, `.venv/bin/das`), Grep, Glob,
synapaxia memory tools, WebSearch (ML research).

**Routes to:** `das-feature-tdd`, `retrieval-design`, `embedding-eval`,
`synapaxia-memory`.

---

## Agent B - `das-operator`

**Role:** Intelligent archivist. Ingests documents into a DAS corpus, retrieves from
it using the validated navigation pattern, and audits corpus health. The embodiment
of `rag-nav-mxbai` with graceful degradation.

**Tools:** Read, Bash (`das` CLI, `find`/`grep`/`ls`, optional `ollama`/ChromaDB
access), Glob, Grep, synapaxia memory tools.

**Routes to:** `rag-nav-retrieval`, `corpus-ingest`, `writing-passport-summaries`,
`corpus-audit`, `synapaxia-memory`.

---

## Skills

### Engineer skills

**`das-feature-tdd`** - The project's development loop. Encodes the CLAUDE.md rule
("every new CLI command needs implementation in `das/cli.py`, test in
`tests/test_cli.py`, an entry in `docs/cli-reference.md`, and a CHANGELOG update"),
the `corpus` fixture / `CliRunner` testing pattern, and the conventions (no em
dashes, minimal deps, `from __future__ import annotations`). Rigid skill: TDD first.

**`retrieval-design`** - How to design or extend retrieval features for the `das`
tool. Summarizes the settled benchmark findings and the rag-nav pattern, lists the
open questions, and points to the research docs. Flexible skill: applies principles
to the design at hand.

**`embedding-eval`** - How to validate an ML/retrieval change empirically against the
external nav-test harness at `~/Projects/das-nav-test/`. Documents `nav-test.py`,
`rag-test.py`, how to add a variant, the variance thresholds (< 1.5 turns = noise,
1.5-3.0 = directional, > 3.0 = strong; use 5+ runs for spec decisions), and the
ChromaDB/Ollama infrastructure. The engineer may run the harness.

### Operator skills

**`rag-nav-retrieval`** - The validated navigation pattern:
1. If Ollama (`:11434`) + a ChromaDB passport collection are available: embed query
   with `mxbai-embed-large`, query passport chunks (top 5 by L2), take best hit,
   resolve `das_address` to folder path, navigate from that hint.
2. Treat the hint as a suggestion - if folder contents do not match, `ls` parent or
   start from root.
3. For sub-tree enumeration (Q2-class) or when RAG returns nothing: fall back to
   manifest-first (read `das.manifest.yaml`).
4. If neither RAG nor manifest is available: filesystem jump-table navigation using
   numeric address prefixes (already competitive per benchmark).
Answer from file content only.

**`corpus-ingest`** - Add a document to a corpus: choose/assign the address
(`das add`), pick the type from the controlled vocabulary (spec 5.4), write the
passport (delegates the summary to `writing-passport-summaries`), apply tags
selectively (the selective-tag rule - client/market-scoped, out-of-context docs
only), and update the manifest.

**`writing-passport-summaries`** - Wraps the existing guide at
`docs/writing-passport-summaries.md`. The single highest-leverage lever for RAG
routing accuracy: write the summary to answer the questions agents will ask, name
subject/type/entities/facts, enumerate contents for folder-level index passports,
2-5 sentences. Points to the canonical doc rather than duplicating it.

**`corpus-audit`** - Corpus health: run `das validate`, flag missing or generic
passport summaries, missing folder-level index passports (folders with > 3 docs),
and tag hygiene (over-tagged internal docs, inconsistent codes). Reports findings;
does not auto-rewrite without confirmation.

### Shared skill

**`synapaxia-memory`** - Both agents `search_episodes` / `search_procedures` before
starting work and `store_episode` / `store_procedure` after. The operator records
corpus-specific lessons ("corpus X: Q4-class enumeration needs manifest-first"); the
engineer records design decisions and their rationale. This is the only place
synapaxia is touched, and only as agent memory - never for document content.

---

## Data Flow

**Operator retrieval:**
```
user query
  -> synapaxia-memory: recall prior lessons for this corpus
  -> rag-nav-retrieval:
       (Ollama+ChromaDB?) embed (mxbai) -> passport chunks -> das_address -> folder hint
       else -> manifest-first / filesystem jump-table
  -> navigate -> Read relevant files
  -> answer from content
  -> synapaxia-memory: store what worked
```

**Engineer feature work:**
```
task
  -> synapaxia-memory: recall prior design decisions
  -> retrieval-design (if a retrieval feature) -> design grounded in findings
  -> das-feature-tdd: write failing test -> implement -> pytest -> docs + changelog
  -> embedding-eval (if an ML change needs empirical validation) -> run harness
  -> synapaxia-memory: store decision + rationale
```

The DAS address is the durable join key across both flows.

---

## Infrastructure Decisions

- **Document RAG: degrade gracefully.** No embedding/vector infra added to the repo.
  `rag-nav-retrieval` uses Ollama+ChromaDB when present, else manifest-first /
  filesystem navigation. An optional in-repo embedding helper can be added later.
- **Engineer reaches the external harness.** `embedding-eval` documents and may run
  `~/Projects/das-nav-test/` scripts. The harness is outside the repo but on this
  machine; the research docs in `docs/research/` are the committed output.
- **No new plugin.** Agents and skills are project-local markdown files.

---

## Verification

- Agents and skills are markdown; they will be built using the `writing-skills` and
  `agent-development` best practices: sharp trigger descriptions, RFC-2119 phrasing,
  progressive disclosure, no duplication of the research docs.
- Engineer path real verification: the existing `pytest` suite (`.venv/bin/pytest`).
- Operator path verification: a dry-run `corpus-ingest` + `corpus-audit` against a
  throwaway corpus (the `corpus` test fixture or a `tmp_path` copy), confirming
  `das validate` passes and a passport summary routes for a sample query.
- Trigger verification: confirm each agent and skill activates on representative
  prompts before considering the work complete.

---

## Build Order (high level)

1. `synapaxia-memory` (shared dependency for both agents).
2. Operator track: `writing-passport-summaries` -> `corpus-ingest` ->
   `rag-nav-retrieval` -> `corpus-audit` -> `das-operator.md`.
3. Engineer track: `das-feature-tdd` -> `retrieval-design` -> `embedding-eval` ->
   `das-engineer.md`.
4. Trigger + dry-run verification for both agents.

The detailed sequencing, file contents, and per-skill acceptance checks belong in
the implementation plan.
