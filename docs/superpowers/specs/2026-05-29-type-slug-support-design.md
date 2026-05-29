# {type}-slug Support Design

**Date:** 2026-05-29
**Author:** Aaron Lamb (with Claude)
**Status:** Approved design - pending implementation plan

Bring the `das` tool in line with spec v0.3's `{type}` model in two parts: align the
config that `das init` writes to spec section 4, and add opt-in `das validate --strict`
type-slug enforcement. Closes the largest code-vs-spec gap identified in the 2026-05-28
project evaluation.

---

## Goals

1. `das init` writes a spec-section-4-conformant config (no old-scheme remnants).
2. The tool understands the 15-type controlled vocabulary (spec section 5.4) and can
   enforce the `{type}` component of filenames, opt-in, without breaking legacy corpora.

## Non-Goals

- Descriptor-presence enforcement, folder-label format enforcement, and a file-creation
  command (`das new`). These are explicit follow-ups that can layer onto `--strict` and
  the new type constant later.
- A package version bump or `SPEC_VERSION` rename (tracked separately).
- Removing or changing the `org` config field (it remains, per spec section 4).
- Per-corpus extensibility of the type vocabulary. The list is a hard-capped spec-level
  constant (spec section 5.4: "new types require explicit addition to this table").

## Key Decisions (locked)

- **Remove** the `--context-type` / `--date-format` CLI options outright (they are inert
  today - nothing reads them). Not deprecated no-ops. A script passing them will get a
  "no such option" error; acceptable for a POC and correct per spec.
- **`VALID_TYPE_SLUGS` lives in `das/manifest.py`** alongside the address grammar (lowest
  level module, no package deps, reusable by a future `das new`).
- **Type enforcement is opt-in via `das validate --strict`.** Default `das validate` is
  unchanged and never newly-fails a corpus that was passing. Tag enforcement stays
  on-by-default (already shipped; safe because it only fires when a `tags` vocabulary is
  defined). `--strict` is a superset: all default checks plus type enforcement.

---

## Part 1 - Config alignment in `das init`

**Change:**
- Remove `context_type` and `date_format` fields from `DASConfig` (`das/config.py`).
- Remove `VALID_CONTEXT_TYPES` and the `context_type` validation in `__post_init__`.
  (Keep the `address_separator == "."` enforcement.)
- Remove the `--context-type` and `--date-format` options from the `init` command
  (`das/cli.py`) and stop passing them into `DASConfig`.

**Result:** `das init` writes `version, corpus, initialized, org?, tags?,
address_separator, manifest` - matching spec section 4.

**Backward compatibility (free):** existing `das.config.yaml` files that contain
`context_type` / `date_format` still load. `load_config` filters unknown keys via the
dataclass `fields()` set, so the dropped keys are silently ignored. No migration, no
breakage. Verified: neither field is used to generate or validate anything today (only
`context_type` had a value check; `date_format` was inert with a default of `YYMMDD`).

---

## Part 2 - Type vocabulary constant

Add to `das/manifest.py`:

```python
VALID_TYPE_SLUGS = {
    "runbook", "plan", "spec", "design", "strategy", "playbook", "proposal",
    "contract", "report", "catalog", "lead", "post", "template", "reference",
    "procedure",
}
```

Single source of truth, matching spec section 5.4 exactly (15 types). A `frozenset`/`set`
for O(1) membership. Reusable by the validator now and a future `das new`.

---

## Part 3 - `das validate --strict` type enforcement

**CLI:** add a `--strict` boolean option (default `False`) to the `validate` command.
Pass it through to `validate_corpus(corpus_root, strict=False)`.

**Default mode (`strict=False`):** unchanged behavior - address grammar, manifest
cross-check, root-file cross-check, malformed-prefix messages, and tag-vocabulary check
(when a vocabulary is defined). Legacy corpora are unaffected.

**Strict mode (`strict=True`):** all default checks PLUS, for each addressed FILE, the
`{type}` token must be a member of `VALID_TYPE_SLUGS`; otherwise a `ValidationError`.

**Type extraction (reuses the tag-extraction approach):**
1. Take the remainder after the `{address}-` prefix.
2. Split on `-`.
3. If the first token matches `TAG_CODE_RE` (uppercase 2-5, i.e. a tag), the type
   candidate is the SECOND token; otherwise the first token.
4. If the type candidate is not in `VALID_TYPE_SLUGS`, append
   `ValidationError(path, f"Invalid or missing type slug '{candidate}' (not in the spec section 5.4 vocabulary)")`.
   If there is no type candidate at all (e.g. a bare `{address}-` with nothing after, or
   only a tag and nothing else), report the same error with an empty/absent candidate.

Examples:
- `02.01.04-ULS-runbook-netbird-ztna.md` -> tag `ULS`, type candidate `runbook` -> valid.
- `07.08-spec-hexpublish.md` -> type candidate `spec` -> valid.
- `00-reference-company-profile.md` -> type candidate `reference` -> valid.
- `02.01.01-ATL-NSL-msa-260301.pdf` (legacy) -> tag `ATL`, type candidate `NSL` -> invalid
  (correctly fails `--strict`).
- `00-orphan.md` -> type candidate `orphan` -> invalid (missing a real type).

**Folders are exempt** (folder format is `{address}-{Label}`, no type), consistent with
tag enforcement - the type check lives in the file branch only.

**Reuse:** import `TAG_CODE_RE` and `VALID_TYPE_SLUGS` from `das.manifest` /
`das.config` as appropriate (no duplication). The tag extraction added for tag
enforcement and the type extraction share the "first-token-is-tag?" logic; factor a small
helper if it reduces duplication, but do not over-engineer.

---

## Data Flow

```
das validate [--strict]
  -> validate_corpus(root, strict)
       load config (tags vocabulary, if any)
       walk files/folders (existing skip rules)
       per addressed file:
         - address grammar + manifest/parent cross-check   (always)
         - tag in vocabulary?                               (when vocab defined)
         - type slug in VALID_TYPE_SLUGS?                   (only when strict)
  -> errors -> formatted, non-zero exit (existing behavior)
```

---

## Error Handling

- Strict-mode type violations are ordinary `ValidationError`s - collected, formatted, and
  cause a non-zero exit exactly like existing errors. No new error channel.
- `--strict` with a non-initialized directory behaves like plain `validate` (the existing
  "no DAS corpus found" path).

---

## Testing

**Config (Part 1):**
- `das init` writes a config with NO `context_type` / `date_format` keys.
- A hand-written config that DOES contain those keys still loads (keys filtered, no error).
- `das init --context-type x` now exits non-zero with "no such option" (option removed).

**Validate default (Part 3):**
- A corpus with legacy/old-format files validates exactly as before - no type errors
  introduced in default mode.

**Validate --strict (Part 3):**
- Valid type slug (`...-runbook-...`) -> clean.
- Invalid/unknown type (`...-frobnicate-...`) -> error.
- Tag + valid type (`...-ULS-runbook-...`, ULS in vocab) -> clean.
- Legacy file (`...-ATL-NSL-msa-260301.pdf`) -> error.
- Missing type (`00-orphan.md`) -> error.
- A folder with an uppercase-looking label is NOT type-checked.
- `das validate --strict` exit codes (clean vs violations).

**Constant:**
- `VALID_TYPE_SLUGS` contains exactly the 15 spec section 5.4 types.

---

## Docs / Changelog

- `docs/cli-reference.md`: document `--strict` on `validate`; update the `init` command
  (remove the `--context-type` / `--date-format` options).
- `docs/concepts.md`: drop `context_type` / `date_format` from the config-field table;
  note `das validate --strict` type enforcement.
- `docs/spec.md`: touch only if something becomes inaccurate (it should not).
- `CHANGELOG.md`: `### Added` for `--strict` + type vocabulary; `### Removed` (or
  `### Changed`) for the dropped init options.

---

## Build Order (high level)

1. Part 2 constant (`VALID_TYPE_SLUGS` in `manifest.py`) - dependency for Part 3.
2. Part 1 config alignment (`config.py` + `cli.py` init) with tests.
3. Part 3 `--strict` type enforcement (`validator.py` + `cli.py` validate) with tests.
4. Docs + changelog.

Detailed task-by-task sequencing, exact test code, and the type-extraction helper belong
in the implementation plan.
