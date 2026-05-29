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
