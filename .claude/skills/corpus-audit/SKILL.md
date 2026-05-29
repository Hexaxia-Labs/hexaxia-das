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
