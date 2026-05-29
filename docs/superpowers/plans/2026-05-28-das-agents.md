# DAS Agents Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build two project-local Claude Code agents (`das-engineer`, `das-operator`) plus an 8-skill library under `hexaxia-das/.claude/`, wiring both agents to synapaxia for memory.

**Architecture:** Thin router agents in `.claude/agents/`; small focused skills in `.claude/skills/<name>/SKILL.md`. The operator embodies the validated `rag-nav` navigation pattern with graceful degradation to manifest-first / filesystem navigation. The engineer carries the settled benchmark findings and can run the external nav-test harness. synapaxia is used only as agent memory (episodes + procedures), never for document content. No new plugin, no new repo dependencies.

**Tech Stack:** Markdown (skill/agent definitions), the existing `das` Typer CLI, synapaxia MCP tools, Ollama + ChromaDB (optional, for the operator's RAG path). Verification uses `.venv/bin/das`, `.venv/bin/pytest`, and trigger checks.

**Artifact note:** Deliverables are markdown. Each task creates one file with complete content, verifies its structure, and commits. There is no red-green test cycle for the markdown itself; the engineer's TDD discipline lives inside the `das-feature-tdd` skill content. Task 11 performs trigger + dry-run verification across the whole set.

**Reference docs the skills point to (do not duplicate their content):**
- `docs/writing-passport-summaries.md` - passport summary guide
- `rag-testing-methods.md` - RAG infrastructure, chunk format, query flow
- `docs/research/nav-test-findings-260528.md` - 12 findings, 8 recommendations
- `docs/research/benchmark-design-260528.md` - question taxonomy, variance thresholds, open questions
- `docs/research/naming-convention-analysis-260528.md` - per-element signal analysis, tag guidance
- `docs/spec.md` - DAS spec v0.3 (type vocabulary 5.4, tags 5.3)

**Known facts the content must respect (verified against the codebase):**
- `das` commands: `init`, `add <address> <label> <description> [--agent-hint] [--path]`, `ls [address]`, `find <query>`, `validate`. Run as `.venv/bin/das`.
- `das add` registers a **manifest node** (a folder address). It does **not** place files or write passports. Naming a file `{address}-{type}-{descriptor}.ext` and writing its passport HTML-comment block are manual agent steps.
- Type vocabulary (spec 5.4, hard-capped 15): `runbook, plan, spec, design, strategy, playbook, proposal, contract, report, catalog, lead, post, template, reference, procedure`.
- Manifest node types (auto-inferred by depth): `area, category, subcategory, context`.
- RAG infra on this machine: Ollama at `/usr/local/bin/ollama` (port 11434), ChromaDB at `~/Projects/sage/.claude/rag/chroma_db`. Test collections `das_nav_test_nomic` / `das_nav_test_mxbai` exist; a general corpus needs its own collection, so the operator degrades to manifest/filesystem unless a corpus is embedded.
- synapaxia MCP tools: `mcp__synapaxia__search_episodes`, `mcp__synapaxia__search_procedures`, `mcp__synapaxia__store_episode`, `mcp__synapaxia__store_procedure`, `mcp__synapaxia__hybrid_search`.

---

## File Structure

```
.claude/
  agents/
    das-engineer.md
    das-operator.md
  skills/
    synapaxia-memory/SKILL.md
    writing-passport-summaries/SKILL.md
    corpus-ingest/SKILL.md
    rag-nav-retrieval/SKILL.md
    corpus-audit/SKILL.md
    das-feature-tdd/SKILL.md
    retrieval-design/SKILL.md
    embedding-eval/SKILL.md
  README.md                # short index of the agents/skills (Task 11)
```

Build order: shared skill first (both agents depend on it), then the operator track (its skills reference each other), then the engineer track, then the two agent files, then verification.

---

### Task 1: `synapaxia-memory` skill (shared)

**Files:**
- Create: `.claude/skills/synapaxia-memory/SKILL.md`

- [ ] **Step 1: Create the skill file**

```markdown
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
```

- [ ] **Step 2: Verify structure**

Run: `head -5 .claude/skills/synapaxia-memory/SKILL.md`
Expected: frontmatter with `name: synapaxia-memory` and a `description:` line.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/synapaxia-memory/SKILL.md
git commit -m "feat: add synapaxia-memory shared skill"
```

---

### Task 2: `writing-passport-summaries` skill (operator)

**Files:**
- Create: `.claude/skills/writing-passport-summaries/SKILL.md`

- [ ] **Step 1: Create the skill file**

```markdown
---
name: writing-passport-summaries
description: Use when writing or improving a DAS document passport summary, or when RAG keeps missing the right document for a corpus. The passport summary field is the entire RAG routing signal. Triggers on "passport", "summary", "why isn't RAG finding this", "improve routing", or when filing a document into a DAS corpus.
---

# writing-passport-summaries

The passport `summary` field is the single highest-leverage lever for RAG routing
accuracy. It is the only content the embedding model sees. The full guide lives at
**`docs/writing-passport-summaries.md`** - read it before writing summaries. This skill
is the operational checklist; the doc is the canonical reference with worked examples.

## The rule

Write the summary to answer the questions an agent will ask about this document - not to
describe what the document is.

## Checklist

1. Name the subject directly. No "This document describes...", no "Comprehensive overview".
2. Include key entities: client name, product, people, org codes, addresses it touches.
3. Include key facts: counts, dates, statuses, amounts, blockers - the things queries hit.
4. For folder-level index passports, **enumerate the contained items** with their
   addresses and statuses. This is what answers enumeration (Q4-class) questions from RAG
   alone, with zero navigation turns.
5. Match the vocabulary of likely queries (the model routes on semantic proximity).
6. Length: 2-5 sentences / 50-150 words. Over ~300 words dilutes the signal.

## Test before filing

For each summary, identify the 2-3 queries that should route here, then confirm the
summary contains those words/concepts. If not, add them. The benchmark's one mxbai miss
(Q4, ULS active projects) was a folder summary that said "United Life Services client
folder" but never named the projects - so it lost to a doc mentioning "active posts".

## Format reference

See `docs/writing-passport-summaries.md` for the full passport block format and per
question-class good/poor examples. Type vocabulary is in `docs/spec.md` 5.4.
```

- [ ] **Step 2: Verify structure**

Run: `head -5 .claude/skills/writing-passport-summaries/SKILL.md`
Expected: frontmatter with `name: writing-passport-summaries` and a `description:` line.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/writing-passport-summaries/SKILL.md
git commit -m "feat: add writing-passport-summaries skill"
```

---

### Task 3: `corpus-ingest` skill (operator)

**Files:**
- Create: `.claude/skills/corpus-ingest/SKILL.md`

- [ ] **Step 1: Create the skill file**

```markdown
---
name: corpus-ingest
description: Use when adding a document to a DAS corpus - assign its address, pick the controlled type slug, name the file, write the passport block, apply tags selectively, and register the node. Triggers on "add a document", "ingest this", "file this doc", "where does this go", "give this an address".
---

# corpus-ingest

Add a document to a DAS corpus correctly the first time. Order matters: decide the
address, then the type, then the filename, then the passport, then register the node.

## Steps

1. **Find the right address.** Read `das.manifest.yaml` (or run `.venv/bin/das ls`) to see
   the existing tree. Pick the deepest existing parent the document belongs under. If a new
   folder address is needed, choose the next free `.NN` under that parent.

2. **Register the node if the address is new** (folders only):
   `.venv/bin/das add <address> <Label> "<one-sentence description>" [--agent-hint "..."]`
   Note: `das add` only writes the manifest node. It does NOT place the file or write the
   passport - those are steps 3-5.

3. **Pick the type slug** from the hard-capped vocabulary (spec 5.4):
   `runbook, plan, spec, design, strategy, playbook, proposal, contract, report, catalog,
   lead, post, template, reference, procedure`. If nothing fits, stop and ask - do not
   invent a type. New types require a spec change.

4. **Name the file** `{address}-{type}-{descriptor}.ext`. Keep the descriptor specific
   enough to carry search signal (avoid over-truncating words that appear in likely
   queries). The folder address prefix is not required on the file's folder - the filename
   carries the jump-table signal (benchmark finding 11).

5. **Write the passport block** at the top of the file (Markdown HTML comment). Delegate the
   `summary` field to the `writing-passport-summaries` skill - it is the RAG signal.
   \`\`\`markdown
   <!--
   passport:
     title: "Specific title that would appear in search"
     type: runbook
     status: active        # active | draft | deprecated | archived
     tags: [uls]           # see step 6 - selective only
     das_address: "02.01.04"
     created: "YYYY-MM-DD"
     modified: "YYYY-MM-DD"
     summary: "2-5 sentences answering the questions agents will ask. See the
               writing-passport-summaries skill."
   -->
   \`\`\`

6. **Apply tags selectively** (spec 5.3 Rule 6 / naming-convention-analysis). Tag only
   client- or market-scoped, out-of-context documents that surface in git log, search
   results, tickets, or email. Do NOT tag internal admin/product/marketing docs - tags add
   parsing cost to every `ls` of the folder (benchmark finding 10). Use the corpus tag
   vocabulary from `das.config.yaml`.

7. **Update folder-level index passport** if this folder now has more than 3 documents and
   the index summary no longer enumerates contents. Re-run `writing-passport-summaries`.

8. **Validate:** `.venv/bin/das validate`. Resolve any errors before finishing.
```

- [ ] **Step 2: Verify structure**

Run: `head -5 .claude/skills/corpus-ingest/SKILL.md`
Expected: frontmatter with `name: corpus-ingest` and a `description:` line.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/corpus-ingest/SKILL.md
git commit -m "feat: add corpus-ingest skill"
```

---

### Task 4: `rag-nav-retrieval` skill (operator)

**Files:**
- Create: `.claude/skills/rag-nav-retrieval/SKILL.md`

- [ ] **Step 1: Create the skill file**

```markdown
---
name: rag-nav-retrieval
description: Use when retrieving or answering a question from a DAS corpus - finding which document holds an answer, or navigating to the right address. Implements the validated rag-nav pattern with graceful fallbacks. Triggers on "find the doc about", "where is", "what does the corpus say about", "look up in the corpus", or any content question against an addressed corpus.
---

# rag-nav-retrieval

The validated navigation pattern for DAS corpora (benchmark: rag-nav-mxbai is -33% turns
vs blind). Use the strongest path available, degrade gracefully, and always answer from
file content - never from the passport summary alone.

## Path A - RAG pre-query (best, when available)

Available only if Ollama (port 11434) is up AND the corpus has been embedded into a
ChromaDB passport collection. See `rag-testing-methods.md` for the embed pipeline.

1. Embed the user query with `mxbai-embed-large` via Ollama
   (`POST http://localhost:11434/api/embeddings`). mxbai routes 7/8 vs nomic 3/8 - use mxbai.
2. Query passport chunks only: `where={"chunk_type": "passport"}`, top 5 by L2 distance.
3. Take the best hit, extract `das_address` from its metadata.
4. Resolve the address to a folder path (scan corpus root for a folder name starting with
   `{das_address}-`, or read the manifest).
5. Treat it as a hint: `ls` that path first. If contents don't match the question, `ls` the
   parent or start from root.

## Path B - manifest-first (fallback, and preferred for sub-tree enumeration)

Use when RAG is unavailable, returns nothing, or the question is a sub-tree enumeration
(Q2-class, e.g. "list all scheduled LinkedIn posts") - manifest beats RAG there (Q2 misroute).

1. Read `das.manifest.yaml`. It is the full address map.
2. Match the question to a label/description; route directly to that address's folder.
3. `.venv/bin/das find <term>` and `.venv/bin/das ls <address>` help narrow.

## Path C - filesystem jump-table (always available)

Use when there is no manifest and no RAG.

1. `ls .` at corpus root. Numeric prefixes (`00-Admin 01-Finance 02-Clients ...`) are a
   jump-table - discard irrelevant areas immediately and descend the relevant one.
2. The `{type}` slug in filenames tells you document intent without opening
   (`...-runbook-...`, `...-report-...`). Read only relevant files.

## Discovery (enumerate all docs for an entity)

When asked to list every document for a client/category, prefer filename tag search:
`find . -name '*-TAG-*' -type f` (benchmark: -56% vs blind). Passport grep
(`grep -rl 'tag' .`) works only when the tag string is distinctive.

## Always

- Answer from the content of files you actually Read, not from passport summaries.
- Before starting, recall via the `synapaxia-memory` skill; after, store what worked
  (e.g. which path won for this question class on this corpus).
```

- [ ] **Step 2: Verify structure**

Run: `head -5 .claude/skills/rag-nav-retrieval/SKILL.md`
Expected: frontmatter with `name: rag-nav-retrieval` and a `description:` line.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/rag-nav-retrieval/SKILL.md
git commit -m "feat: add rag-nav-retrieval skill"
```

---

### Task 5: `corpus-audit` skill (operator)

**Files:**
- Create: `.claude/skills/corpus-audit/SKILL.md`

- [ ] **Step 1: Create the skill file**

```markdown
---
name: corpus-audit
description: Use to check DAS corpus health - run validation, find missing or generic passport summaries, missing folder-level index passports, and tag-hygiene problems. Triggers on "audit the corpus", "check corpus health", "validate the corpus", "check the passports", "is this DAS-compliant".
---

# corpus-audit

Assess a DAS corpus and report issues. Report findings; do not auto-rewrite files without
the user's confirmation.

## Checks

1. **Naming + manifest validation:** `.venv/bin/das validate`. Report every error with its
   path. This covers address regex, filename format, and manifest cross-checks.

2. **Missing passports:** find content files lacking a passport block.
   `grep -rL 'passport:' --include='*.md' .` (excluding `_`-prefixed drafts and hidden dirs).

3. **Generic summaries:** flag passport summaries that match anti-patterns from
   `docs/writing-passport-summaries.md`: "This document describes", "Comprehensive overview",
   "Contains information about", or summaries with no counts/entities/dates. These are the
   highest-leverage fixes for RAG accuracy.

4. **Missing folder-level index passports:** any folder with more than 3 documents should
   have an index doc whose summary enumerates the folder's contents. Flag folders that lack
   one or whose index summary does not enumerate.

5. **Tag hygiene** (spec 5.3 Rule 6): flag internal admin/product/marketing docs that carry
   tags (tags add nav cost there), and client/market-scoped docs that lack the expected tag.
   Check tag codes against the vocabulary in `das.config.yaml`.

## Output

Produce a short report grouped by check, worst-first (generic/missing summaries first, since
they hurt retrieval most). For each finding give the path and the concrete fix. Offer to
apply fixes via `corpus-ingest` / `writing-passport-summaries` after confirmation.

Recall and store via `synapaxia-memory` around the audit.
```

- [ ] **Step 2: Verify structure**

Run: `head -5 .claude/skills/corpus-audit/SKILL.md`
Expected: frontmatter with `name: corpus-audit` and a `description:` line.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/corpus-audit/SKILL.md
git commit -m "feat: add corpus-audit skill"
```

---

### Task 6: `das-operator` agent

**Files:**
- Create: `.claude/agents/das-operator.md`

- [ ] **Step 1: Create the agent file**

```markdown
---
name: das-operator
description: Operates real DAS corpora - ingests and addresses documents, writes passports, retrieves answers via the validated rag-nav pattern, and audits corpus health. Use when the user wants to file, find, organize, retrieve from, or audit documents in a DAS-addressed corpus. Not for developing the das tool itself - use das-engineer for that.
tools: Read, Glob, Grep, Bash, mcp__synapaxia__search_episodes, mcp__synapaxia__search_procedures, mcp__synapaxia__store_episode, mcp__synapaxia__store_procedure, mcp__synapaxia__hybrid_search
---

You are the DAS operator - an intelligent archivist for document corpora organized by the
Hexaxia Document Addressing Standard. You operate corpora; you do not develop the `das` tool
(that is das-engineer's job).

## How you work

Start every task by recalling prior lessons with the `synapaxia-memory` skill, and end by
storing what you learned. Then route to the skill that fits the task:

- **Filing / adding a document** -> `corpus-ingest` (which calls `writing-passport-summaries`).
- **Answering a question / finding a document** -> `rag-nav-retrieval`.
- **Improving a passport, or RAG is missing docs** -> `writing-passport-summaries`.
- **Checking corpus health** -> `corpus-audit`.

## Principles (from the closed benchmark - do not relitigate)

- Numeric address prefixes are a jump-table; use them to discard irrelevant areas fast.
- The passport `summary` is the entire RAG signal - quality there beats everything else.
- Apply tags selectively (client/market-scoped, out-of-context docs only).
- Answer from file content you actually read, never from a passport summary alone.
- Prefer the strongest retrieval path available, but degrade gracefully: RAG -> manifest ->
  filesystem jump-table. For sub-tree enumeration, manifest-first beats RAG.

## CLI

Use `.venv/bin/das` (`init`, `add`, `ls`, `find`, `validate`). `das add` registers a manifest
node only; placing files and writing passports are your manual steps. Run `das validate`
before declaring an ingest or edit complete.

When a request is actually about changing the `das` tool's behavior, say so and recommend
das-engineer rather than editing code yourself.
```

- [ ] **Step 2: Verify structure**

Run: `head -4 .claude/agents/das-operator.md`
Expected: frontmatter with `name: das-operator`, a `description:`, and a `tools:` line.

- [ ] **Step 3: Commit**

```bash
git add .claude/agents/das-operator.md
git commit -m "feat: add das-operator agent"
```

---

### Task 7: `das-feature-tdd` skill (engineer)

**Files:**
- Create: `.claude/skills/das-feature-tdd/SKILL.md`

- [ ] **Step 1: Create the skill file**

```markdown
---
name: das-feature-tdd
description: Use when implementing or modifying any das CLI command or module - the project's test-driven loop. Enforces failing test first (tests/test_cli.py with the corpus fixture and CliRunner), then minimal implementation in das/, then docs and changelog. Triggers on "add a command", "fix das", "implement", "change the manifest/validator/config", "new feature for the tool".
---

# das-feature-tdd

The development loop for the `das` Python tool. Rigid skill - follow the order. Tests fail
before code exists; code is minimal; docs and changelog are part of "done".

## Loop

1. **Write the failing test first** in `tests/test_cli.py`. Use the `corpus` fixture
   (a `tmp_path` with a pre-written config + empty manifest) and Typer's `CliRunner` to
   invoke commands in-process. Do not shell out. Follow the existing test patterns.
2. **Run it and confirm it fails for the right reason:**
   `.venv/bin/pytest tests/test_cli.py::<test_name> -v`
3. **Write the minimal implementation** in the right module:
   - `das/cli.py` - the Typer command (thin shim; translate errors to `typer.Exit(1)` with
     `err=True`).
   - `das/manifest.py` - address/node logic.
   - `das/config.py` - corpus header logic.
   - `das/validator.py` - corpus-walk validation rules.
   Keep logic in the data/operation modules, not in the CLI shim, so tests exercise it
   without subprocess overhead.
4. **Run the test and confirm it passes**, then run the full suite: `.venv/bin/pytest`.
5. **Update docs and changelog (required for every new CLI command):**
   - `docs/cli-reference.md` - add the command entry.
   - `CHANGELOG.md` - add a line under `## [Unreleased]`.
6. **Commit** with a `<type>: <description>` message (feat, fix, docs, test, refactor).

## Conventions (enforced by convention, not tooling)

- `from __future__ import annotations`, dataclasses, type hints.
- No third-party deps beyond `typer` / `pyyaml` (plus `pytest` for dev).
- No em dashes anywhere - use ` - ` (hyphen with spaces) or reword.
- `das.config.yaml` is immutable after init; the manifest is append-mostly (retire with
  `deprecated: true`, never delete). Changing `config.py` field semantics is spec-breaking.

Recall/store design rationale via `synapaxia-memory`. For retrieval/naming feature design,
consult `retrieval-design` first. For empirical ML validation, use `embedding-eval`.
```

- [ ] **Step 2: Verify structure**

Run: `head -5 .claude/skills/das-feature-tdd/SKILL.md`
Expected: frontmatter with `name: das-feature-tdd` and a `description:` line.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/das-feature-tdd/SKILL.md
git commit -m "feat: add das-feature-tdd skill"
```

---

### Task 8: `retrieval-design` skill (engineer)

**Files:**
- Create: `.claude/skills/retrieval-design/SKILL.md`

- [ ] **Step 1: Create the skill file**

```markdown
---
name: retrieval-design
description: Use when designing or extending the das tool's retrieval, naming, or RAG-related features. Summarizes the settled benchmark findings and the open questions so design builds on evidence instead of re-deriving it. Triggers on "add semantic search", "improve find", "should we embed", "retrieval feature", "naming change", "manifest vs RAG".
---

# retrieval-design

Design retrieval/naming features for the `das` tool from evidence. The navigation benchmark
is a **closed study** (`docs/research/benchmark-design-260528.md`); its findings are settled.
Build on them - do not relitigate. Then hand off to `das-feature-tdd` to implement.

## Settled findings (use as constraints)

1. Numeric address prefixes earn their keep - descriptive/alphabetical naming is +30% worse.
   Keep numeric prefixes in any naming proposal.
2. `mxbai-embed-large` routes 7/8 vs nomic 3/8. Embedding-model choice is the highest-leverage
   RAG variable. Default to mxbai for any DAS RAG work.
3. The passport `summary` field is the entire RAG signal. Features that improve summary
   quality or coverage beat features that tune chunking/formatting.
4. Folder address prefixes are NOT required - the filename carries the jump-table signal
   (real-v3 = das). Do not require folder renames for adoption.
5. Tags help targeted enumeration but cost broad navigation - selective application only.
6. `rag-nav-mxbai` is the best navigation pattern overall; `das-manifest` wins sub-tree
   enumeration (Q2). A hybrid (RAG, fall back to manifest) is the recommended default.

## Open questions (the frontier - design here adds value)

From `benchmark-design-260528.md`: larger corpora scaling, mixed adoption, passport+RAG for
discovery, better summaries closing the Q4 miss, a manifest+RAG hybrid, longer runs for
significance, and cost-per-correct-answer measurement.

## Process

1. Recall prior design decisions via `synapaxia-memory`.
2. State which settled finding(s) the feature respects and which open question (if any) it
   advances. Cite the research doc.
3. Sketch the smallest design that fits the spec and the existing module boundaries
   (`config`, `manifest`, `validator`, `cli`). Honor YAGNI and the minimal-deps rule.
4. If the design makes an empirical claim ("this embedding helps", "this naming is faster"),
   plan validation with `embedding-eval` before committing it to the spec.
5. Hand off to `das-feature-tdd` for implementation. Store the decision + rationale.

Read `nav-test-findings-260528.md` and `naming-convention-analysis-260528.md` for the detail
behind any finding before designing against it.
```

- [ ] **Step 2: Verify structure**

Run: `head -5 .claude/skills/retrieval-design/SKILL.md`
Expected: frontmatter with `name: retrieval-design` and a `description:` line.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/retrieval-design/SKILL.md
git commit -m "feat: add retrieval-design skill"
```

---

### Task 9: `embedding-eval` skill (engineer)

**Files:**
- Create: `.claude/skills/embedding-eval/SKILL.md`

- [ ] **Step 1: Create the skill file**

```markdown
---
name: embedding-eval
description: Use when an ML or retrieval change needs empirical validation against the DAS nav-test benchmark harness. Documents the external harness, how to add a variant, and how to read results. Triggers on "benchmark this", "does this embedding help", "measure navigation cost", "run nav-test", "validate the retrieval change".
---

# embedding-eval

Validate a retrieval/ML change empirically against the navigation benchmark before citing it
in the spec. The harness is a **separate local project, not in this repo**, and not on
GitHub. The committed research docs in `docs/research/` are its output.

## Harness location and scripts

`~/Projects/das-nav-test/`
- `nav-test.py` - main runner; calls `rag_lookup()` inline for rag-nav variants.
- `rag-test.py` - embed corpus + test retrieval accuracy (passport hit rate).
- `report.py` - regenerates `RESULTS.md` from run JSONs in `results/`.

Infrastructure: ChromaDB at `~/Projects/sage/.claude/rag/chroma_db` (collections
`das_nav_test_nomic`, `das_nav_test_mxbai`); Ollama on port 11434 (`mxbai-embed-large`,
`nomic-embed-text`). Read `rag-testing-methods.md` in this repo for the full pipeline.

## Running

\`\`\`bash
cd ~/Projects/das-nav-test
# embed (once per model)
python3 rag-test.py --embed --model mxbai
# retrieval accuracy
python3 rag-test.py --query --model mxbai
# full nav benchmark for a variant
RAG_MODEL=mxbai python3 nav-test.py --corpus rag-nav-mxbai
# regenerate the report
python3 report.py
\`\`\`

## Adding a variant

Edit `nav-test.py`: add a `(corpus_path, system_prompt, allowed_tools)` entry to `CORPORA`,
run `python3 nav-test.py --corpus <name>`, then add it to `report.py` (`CORPUS_ORDER`,
`QUESTION_LABELS`) and regenerate. Full steps in `benchmark-design-260528.md`.

## Reading results (variance thresholds)

3 runs per variant is noisy - treat as directional.
- < 1.5 turns/question difference: noise, not signal.
- 1.5-3.0 turns/question: directional, confirms a hypothesis.
- > 3.0 turns/question: strong signal, usable in spec decisions.
Always check the per-question breakdown before citing an aggregate. **Use 5+ runs before any
spec decision.** Turn count is a proxy - it does not measure token cost or latency.

Recall/store outcomes via `synapaxia-memory`. Hand validated findings back to
`retrieval-design` / `das-feature-tdd`.
```

- [ ] **Step 2: Verify structure**

Run: `head -5 .claude/skills/embedding-eval/SKILL.md`
Expected: frontmatter with `name: embedding-eval` and a `description:` line.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/embedding-eval/SKILL.md
git commit -m "feat: add embedding-eval skill"
```

---

### Task 10: `das-engineer` agent

**Files:**
- Create: `.claude/agents/das-engineer.md`

- [ ] **Step 1: Create the agent file**

```markdown
---
name: das-engineer
description: AI/ML engineer for the das tool itself - designs and implements retrieval and naming features with TDD, grounded in the closed benchmark findings, and can validate ML changes against the nav-test harness. Use when building, fixing, or extending the das CLI or its modules. Not for operating document corpora - use das-operator for that.
tools: Read, Edit, Write, Glob, Grep, Bash, WebSearch, mcp__synapaxia__search_episodes, mcp__synapaxia__search_procedures, mcp__synapaxia__store_episode, mcp__synapaxia__store_procedure, mcp__synapaxia__hybrid_search
---

You are the DAS engineer - a full-spectrum AI/ML engineer for the `das` tool. You research
and design retrieval approaches, write specs, and implement them with tests. You build the
tool; you do not operate document corpora (that is das-operator's job).

## How you work

Recall prior design decisions with `synapaxia-memory` before starting, and store decisions +
rationale after. Then route:

- **Designing a retrieval/naming/RAG feature** -> `retrieval-design` (grounds the design in
  benchmark evidence), then `das-feature-tdd` to implement.
- **Implementing or fixing any command/module** -> `das-feature-tdd` (failing test first).
- **An empirical ML claim needs proof** -> `embedding-eval` (the external nav-test harness).

## Settled findings (build on these - the benchmark is a closed study)

- Numeric address prefixes earn their keep (descriptive naming +30% worse).
- mxbai-embed-large routes 7/8 vs nomic 3/8 - embedding model is the top RAG variable.
- The passport `summary` field is the entire RAG signal.
- Folder address prefixes are not required; the filename carries the jump-table signal.
- Tags help targeted enumeration, cost broad navigation - apply selectively.

## Open questions (the frontier)

Larger corpora scaling, mixed adoption, passport+RAG for discovery, better summaries closing
the Q4 miss, a manifest+RAG hybrid, longer benchmark runs, cost-per-correct-answer. See
`docs/research/benchmark-design-260528.md`.

## Conventions

`.venv/bin/pytest` to test, `.venv/bin/das` to exercise the CLI. Match existing style
(`from __future__ import annotations`, dataclasses, type hints). No deps beyond typer/pyyaml.
No em dashes. Every new CLI command needs implementation + test + `docs/cli-reference.md`
entry + `CHANGELOG.md` update. The config is immutable after init; the manifest is
append-mostly.

When a request is actually about operating a corpus (filing, finding, auditing documents),
recommend das-operator rather than doing it here.
```

- [ ] **Step 2: Verify structure**

Run: `head -4 .claude/agents/das-engineer.md`
Expected: frontmatter with `name: das-engineer`, a `description:`, and a `tools:` line.

- [ ] **Step 3: Commit**

```bash
git add .claude/agents/das-engineer.md
git commit -m "feat: add das-engineer agent"
```

---

### Task 11: Verification + index + changelog

**Files:**
- Create: `.claude/README.md`
- Modify: `CHANGELOG.md` (under `## [Unreleased]`)

- [ ] **Step 1: Write the .claude index**

Create `.claude/README.md`:

```markdown
# DAS Agents and Skills

Project-local Claude Code agents and skills for the Hexaxia DAS project.

## Agents (`.claude/agents/`)

- **das-engineer** - AI/ML engineer for the `das` tool. Designs + implements retrieval/naming
  features with TDD, grounded in the closed benchmark findings; can run the nav-test harness.
- **das-operator** - intelligent archivist. Ingests, addresses, retrieves from, and audits
  real DAS corpora using the validated rag-nav pattern.

## Skills (`.claude/skills/`)

| Skill | Owner | Purpose |
|---|---|---|
| synapaxia-memory | shared | Recall/store episodes + procedures around every task |
| writing-passport-summaries | operator | Write the RAG-critical passport summary |
| corpus-ingest | operator | Add a document: address, type, filename, passport, tags |
| rag-nav-retrieval | operator | Validated rag-nav pattern with graceful fallbacks |
| corpus-audit | operator | Corpus health: validate, passports, tag hygiene |
| das-feature-tdd | engineer | The project's test-driven development loop |
| retrieval-design | engineer | Design retrieval features from benchmark evidence |
| embedding-eval | engineer | Validate ML changes against the nav-test harness |

synapaxia is used only as agent memory, never for document content. The operator's RAG path
requires Ollama + an embedded ChromaDB collection and degrades to manifest/filesystem nav.
```

- [ ] **Step 2: Add a changelog entry**

In `CHANGELOG.md`, under `## [Unreleased]`, add:

```markdown
### Added
- Project-local Claude Code agents (`das-engineer`, `das-operator`) and an 8-skill library
  under `.claude/`, wired to synapaxia for agent memory.
```

- [ ] **Step 3: Verify discovery**

Run: `ls .claude/agents/ && ls .claude/skills/`
Expected: 2 agent files (`das-engineer.md`, `das-operator.md`) and 8 skill directories each
containing `SKILL.md`.

Run: `grep -rL '^name:' .claude/agents .claude/skills --include='*.md' || echo "all files have a name field"`
Expected: every agent/skill file has a `name:` frontmatter field (no file listed).

- [ ] **Step 4: Verify no em dashes (project convention)**

Run: `grep -rn '—' .claude/ && echo "FOUND EM DASHES - fix them" || echo "no em dashes"`
Expected: `no em dashes`.

- [ ] **Step 5: Sanity-check the toolchain still works**

Run: `.venv/bin/pytest -q`
Expected: existing suite passes (we changed no Python).

Run: `.venv/bin/das --help`
Expected: CLI help lists `init`, `add`, `ls`, `find`, `validate`.

- [ ] **Step 6: Operator dry-run (manual trigger test)**

In a scratch directory, exercise the operator's path end-to-end without RAG:

```bash
tmp=$(mktemp -d)
.venv/bin/das init scratch-corpus --org SCR --path "$tmp"
.venv/bin/das add 00 Admin "Company governance" --path "$tmp"
.venv/bin/das add 00.01 Business-Registration "Incorporation filings" --path "$tmp"
.venv/bin/das ls --path "$tmp"
.venv/bin/das validate --path "$tmp"
rm -rf "$tmp"
```
Expected: init creates `das.config.yaml` + `das.manifest.yaml`; both `add` calls succeed;
`ls` shows the two nodes; `validate` prints `Corpus is valid.`
This confirms the CLI behaviors the `corpus-ingest` / `corpus-audit` skills depend on.

- [ ] **Step 7: Trigger check (in a fresh session, after reload)**

After `/reload-plugins` (or restarting the session so the new agents/skills are discovered),
confirm:
- Asking "file this runbook into the corpus" surfaces `das-operator` / `corpus-ingest`.
- Asking "add a `das export` command" surfaces `das-engineer` / `das-feature-tdd`.
If a prompt does not trigger the intended skill, sharpen that skill's `description` field
(add the missing trigger phrase) and recommit.

- [ ] **Step 8: Commit**

```bash
git add .claude/README.md CHANGELOG.md
git commit -m "docs: add .claude index and changelog entry for das agents"
```

---

## Self-Review

**Spec coverage:**
- Two agents (das-engineer, das-operator): Tasks 6, 10. ✓
- 8 skills (3 engineer, 4 operator, 1 shared): Tasks 1-5, 7-9. ✓
- synapaxia as memory only: `synapaxia-memory` (Task 1); both agents route through it; scope
  rules forbid document content. ✓
- Operator degrades gracefully (RAG -> manifest -> filesystem): `rag-nav-retrieval` Paths A/B/C
  (Task 4). ✓
- Engineer reaches external harness: `embedding-eval` (Task 9). ✓
- No new plugin / no new deps: all artifacts are project-local markdown; no `pyproject.toml`
  change. ✓
- Verification (pytest, das, dry-run, trigger): Task 11. ✓
- Build order (shared -> operator -> engineer -> agents -> verify): Tasks 1 -> 2-5 -> 7-9 ->
  6/10 -> 11. (Operator agent Task 6 follows its skills; engineer agent Task 10 follows its
  skills.) ✓

**Placeholder scan:** No TBD/TODO. Every file task contains the complete file content. The
only deferred item is the Task 11 Step 7 trigger check, which is an interactive verification
step with a concrete corrective action, not a content placeholder. ✓

**Consistency:** Skill names are referenced identically across agents and skills
(`synapaxia-memory`, `writing-passport-summaries`, `corpus-ingest`, `rag-nav-retrieval`,
`corpus-audit`, `das-feature-tdd`, `retrieval-design`, `embedding-eval`). CLI invocations use
`.venv/bin/das` and `.venv/bin/pytest` throughout. The type vocabulary and the "das add only
registers a node" fact match the verified codebase. synapaxia tool names match the MCP names
listed in the header. ✓
```

