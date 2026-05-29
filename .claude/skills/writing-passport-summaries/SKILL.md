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
