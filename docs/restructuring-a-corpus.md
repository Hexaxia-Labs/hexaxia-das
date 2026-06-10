# Restructuring and Renaming a Corpus

How to change a corpus at the top level - reshape its areas or rename the whole corpus -
without violating the permanence rule, and when that is the wrong move.

## The tension

DAS rests on one hard rule: **addresses are permanent. They never change, never get reused,
never get renumbered** (spec sections 3.1 and 9). That rule is what makes an address a
reliable, forever-valid coordinate. So "altering a corpus at the top level" sounds like a
contradiction - the top level *is* addresses, and addresses do not move.

It is not a contradiction, because the permanence rule exists to protect *things that depend
on addresses*. An address is permanent so that a reference made today still resolves in two
years. If nothing references an address yet, there is nothing to protect and re-addressing
costs nothing. The whole question of top-level alteration reduces to one: **has the corpus
calcified?**

## Why it happens

Top-level alteration is rare, and it usually means the corpus's original framing was wrong or
has been outgrown. Common triggers:

- **The framing inverted.** You scaffolded around an instance and then realized the durable
  thing is the layer above it. (Worked example below: a corpus built around the Northwind client,
  renamed to the Relay framework with Northwind nested as the first implementation.)
- **The corpus identity changed** - a product or division was renamed, merged, or rebranded.
- **A top-level split was wrong** - two areas that should be one, or one that should be two.

This is distinct from ordinary growth (adding an area - use gapped numbering, section 7.5) and
from choosing a filename convention (`corpus-conventions.md`). It is a change to the *identity*
or the *top-level shape* of the address space.

## The decision: young vs calcified

**This is the load-bearing call. Make it first.**

- **Young (not yet calcified):** the docs are still draft, no other document cites these
  addresses, no consumer - a publish pipeline, another corpus, a deployed agent, a person's
  bookmarks - depends on the map, and ideally the repo is still local. Here, **reshape freely
  and now.** Re-addressing is cheap precisely because nothing points at the old addresses. Do
  the reshape before it calcifies; the cost only ever goes up.
- **Calcified (mature):** addresses are referenced in other documents, published, linked,
  cited, or depended on by tooling or people. Here, **do not renumber.** Use deprecate-and-
  migrate: mark the old nodes `deprecated: true` (never delete - sections 6.2 and 9), add the
  new addresses alongside, leave the old ones resolving as forwards, and migrate content
  forward over time. The address you published must keep working.

In one line: **reshape freely while young; deprecate-and-add once mature.** The practical
consequence is that big structural reframes are a young-corpus move. If you suspect the framing
is wrong, fix it early - while it is still seventeen draft files and not seventeen thousand
referenced ones.

## How to handle it (young, free to reshape)

1. **Rename the corpus (identity).** `git mv` the directory so history is preserved. Update the
   `corpus:` slug in both `das.config.yaml` and `das.manifest.yaml` (they must match). Update
   the titles and self-references in `README.md`, `AGENT_CONTEXT.md`, and `CLAUDE.md` so the
   corpus reads as its new identity. Config and manifest are path-independent, so the directory
   rename alone changes nothing inside them - only the slug and the prose do.
2. **Reshape the address space.** Add the new areas and nodes with `das add`. Move docs into
   their new folders. Re-address each moved doc: set its new `das_address` in the passport and
   rename the file to the new address prefix, keeping the tag, type, and descriptor. Renumbering
   existing areas is permitted *here* - in a young corpus - when the scheme demands it, for
   example when the decade slots are full and a new top-level area has no clean home otherwise.
3. **Keep `das validate` clean throughout.** Every moved file's address must match its new
   parent folder; every addressed folder must be in the manifest. Validate after the move.
4. **Record the reshape in `das.migration.md`** at the corpus root - the reserved migration-log
   file (spec section 4.2; the validator skips it). Write what moved where and why. A reshape
   with no migration record is an unexplained discontinuity in the corpus's history; the
   migration file is the audit trail, the way the manifest is the map.
5. **Fix the cross-references.** Prose pointers - `Related:` sections, inline `90.02`-style
   references - go stale the moment addresses change. Sweep and update them. Addressing and the
   manifest are the DAS agent's responsibility; the prose cross-references are a content task and
   may belong to whoever owns the content.
6. **Deprecate, never delete.** If the corpus is even slightly past "young" and you are vacating
   an old address, leave the node `deprecated: true` rather than removing it.

## When NOT to reshape the top level

- The corpus is mature or referenced - use deprecate-and-migrate, not a renumber.
- The change is purely additive (a new area) - use gapped numbering (section 7.5), not a reshape.
- The reframe is speculative - do not churn the top level on a maybe; wait until the new framing
  is actually decided.

## Worked example: Northwind-Project to Relay

The corpus was scaffolded from the Northwind product's engineering spec, so it was framed around
the instance: named `Northwind-Project`, Northwind-first throughout. The strategy docs then
established that the durable product is the **framework** - the governed middleware layer
between a raw API and its consumers, which is API-agnostic - and Northwind is only its first
implementation. The corpus was upside down.

The fix is a top-level alteration: rename the corpus to `Relay` (the framework) and add an
`Implementations` area with Northwind nested inside as "Relay for Northwind." It is the right moment
because the corpus is young - around seventeen docs, all draft, nothing calcified, local git
with no remote - so re-addressing the Northwind-specific docs costs almost nothing. The decade
slots being full means some re-addressing is unavoidable, which is acceptable for exactly that
reason. Framework-level docs stay at the top; only the clearly instance-specific docs move
down. The reshape is recorded in `das.migration.md`, `das validate` stays clean, and the prose
cross-references are swept afterward.

Had the same realization come two years later, with the addresses cited across published
material and tooling, the move would be deprecate-and-migrate instead of a clean rename - far
more expensive. That gap is the whole argument for reshaping early.

## Gotchas discovered in practice

These came out of the Northwind-Project to Relay reshape and are recorded here so they do not
surprise the next person doing this work.

### 1. YAML colon-in-description breaks `yaml.safe_load`

If a node description or `agent_hint` contains `: ` (colon followed by a space), writing it
as an unquoted YAML scalar produces invalid YAML:

```yaml
# BAD - the colon-space triggers a scanner error on load
description: What Relay is: the governed middleware framework
```

The fix: single-quote the value, or use a folded/literal block scalar. In the manifest
tooling this was a `yaml.dump` vs `yaml.safe_dump` bug - `safe_dump` uses SafeDumper which
applies quoting whenever a string value would be ambiguous to a YAML parser. The `das` CLI
was patched (see CHANGELOG `### Fixed`).

**Practical rule:** any description or agent_hint that starts with a noun phrase and contains
a colon is at risk. Descriptions of the form "What X is: the Y" or "The Z: how to W" need
quoting. If you edit the manifest by hand during a reshape, wrap such values in single quotes
or reword to avoid the colon.

**The symptom** is a `yaml.scanner.ScannerError: mapping values are not allowed here` pointing
at the column where the `:` appears. Find all risky lines before committing:

```bash
grep -n ': ' das.manifest.yaml | grep 'description\|agent_hint'
```

### 2. Passports: only `das_address` needs updating on a move

A moved document needs its passport field `das_address` updated to the new address - that is
the only structural passport field a re-address requires. Other fields (`title`, `type`,
`status`, `edition`, `visibility`, `tags`, `summary`) are about the content, not the location,
and are unchanged by a move.

**The gap:** the `das_address` field in the passport and the filename prefix are two separate
things. The filename rename happens at the filesystem level (`git mv`); updating `das_address`
in the passport body is a separate, manual step. It is easy to miss the passport update when
focused on the filesystem. Add a verification pass after moving docs:

```bash
# For each moved doc, confirm the passport das_address matches the new address prefix
grep -r 'das_address:' 05-Implementations/05.01-Northwind/ | grep -v '05\.01'
# Should return nothing if all passport fields were updated
```

**Note on type slugs:** the architect's content docs may use type slugs outside the 17-slug
controlled vocabulary (e.g. `overview`, `roadmap`, `analysis`). These pass default
`das validate` but fail `das validate --strict`. A reshape is a good time to note which docs
carry non-standard slugs so the content owner can remap them in a follow-up pass.

### 3. Cross-references are the content owner's responsibility, not DAS

Addresses change; prose pointers inside document bodies go stale. The DAS agent owns
addressing, filenames, and the manifest. Prose cross-references - `Related:` sections, inline
address pointers, passport summaries that name other docs - are content and belong to whoever
owns the content. Establish this division explicitly before starting a reshape, and hand the
content owner a concrete sweep list (old address → new file path) so the sweep is mechanical
rather than an open-ended search. See the Relay reshape for a worked example of the handoff
(`HANDOFF-ARCHITECT.md` with the sweep list + a verification grep).
