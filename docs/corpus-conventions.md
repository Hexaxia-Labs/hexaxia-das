# Corpus Conventions and Deviations

How a DAS corpus declares its naming convention, when a corpus may deviate from the
default, and how tooling and agents discover and adhere to whatever a corpus declares.

> **Status (2026-06-03).** The principles, the default convention, the machine-readable
> `naming` block in `das.config.yaml`, and the tooling that branches on it (`das validate`,
> `das new`, `das init`) are all current and implemented. The only item still proposed is the
> optional `PreToolUse` Write hook (section 5 step 5). See "Status: what is real today" at the
> end for the exact line.

## 1. The default convention

Every corpus defaults to address-first naming (spec section 5):

```
{address}-[{TAG}-]{type}-{descriptor}.{ext}
```

The leading numeric address is the **jump-table signal**: an agent discards irrelevant
areas by prefix alone, without opening a file. The benchmark is explicit - DAS filenames
carry the navigation signal, and folder address prefixes are not even required for it.
Address-first is the recommended default for every corpus, and deviating from it has a
cost (below).

## 2. Why a corpus deviates

Some corpora serve a goal the default does not optimize for. The motivating case:
**published editorial content** (a blog, an open-source docs site) wants human and SEO
legibility and chronology - the "slug first, date last" convention common for marketing and
content files. Other plausible axes: corpora that import documents with fixed external
identifiers, or external-facing corpora with their own house style.

A deviation is not a license to drift. It is a declared, justified, validated departure.

## 3. The principle: declare, justify, validate, discover

This is the heart of it, and it is the direct fix for a common failure mode - where the
naming convention is stated in `README.md` and `CLAUDE.md`, both pointing at an agent memory
file (`reference_file_naming_convention`) that does not exist. Prose drifts and the source of
truth becomes a dangling pointer.

A deviation is legitimate only when it is all four of:

- **Declared** - in `das.config.yaml`, one machine-readable source of truth. Never in prose
  that can drift, never via a pointer to a file that may move or vanish.
- **Justified** - the config records *why*. Deviating from address-first costs the
  navigation signal; writing the reason down makes the tradeoff explicit and reviewable.
- **Validated** - `das validate` honors the declared convention, so a file that violates it
  fails the build. Adherence is checked, not hoped for.
- **Discoverable** - the agent reads the config on entry (and `AGENT_CONTEXT.md` points at
  it rather than restating it), so the agent knows the rule before it writes a file.

## 4. The declaration: the `naming` block

A corpus declares its convention in `das.config.yaml`:

```yaml
naming:
  style: das-address                                # das-address | slug-date | custom
  pattern_draft:     "{address}-{type}-{slug}.{ext}"
  pattern_published: "{address}-{type}-{slug}-{YYMMDD}.{ext}"
  description: >
    Address-first for agent navigation, slug for legibility. Date (YYMMDD) is added only
    at publish, when it is final. The published URL leads with the slug; the corpus file
    leads with the address - different layers.
```

Fields:

- `style` - a named common style. `das-address` (the default), `slug-date` (legacy
  marketing files), or `custom` (a corpus-specific regex).
- `pattern_draft` / `pattern_published` - the canonical filename templates. A corpus with
  no lifecycle uses a single `pattern`. Tokens: `{address}` `{TAG}` `{type}` `{descriptor}`
  `{slug}` `{YYMMDD}` `{ext}`.
- `description` - the justification. Required when `style` is not `das-address`.

If a corpus declares no `naming` block, it is treated as `das-address` (the default).

## 5. How tooling and agents handle a declared convention

A layered model - soft discovery for understanding, hard tooling for adherence:

1. **Declare** - the `naming` block in `das.config.yaml`.
2. **Discover** - the agent reads the config on entry; `AGENT_CONTEXT.md` and `CLAUDE.md`
   reference the block instead of restating the rule.
3. **Validate** - `das validate` branches on `style` and applies the matching rules.
   `das-address` uses the current `FILE_ADDRESS_RE` / `FOLDER_NAME_RE` (and strict
   type/descriptor) checks. A `custom` pattern compiles to a regex. Drift fails the build.
4. **Generate** - `das new` produces a compliant filename from the pattern, so compliance
   is the default path and the agent never hand-names a file.
5. **Block (optional, strongest)** - a pre-write validation hook in your agent or editor
   tooling rejects a filename that does not match the declared pattern, so a non-compliant
   file physically cannot be saved.

## 6. The composed convention (the recommended way to deviate for content)

You usually do **not** have to abandon the address to gain legibility - compose them:

```
{address}-{type}-{slug}-{YYMMDD}.{ext}
01.01.01-post-you-have-a-corpus-260603.md
```

- It **validates today**: `DESCRIPTOR_RE` allows digits, so `you-have-a-corpus-260603` is a
  valid descriptor. The address parses first; the date is the tail of the descriptor.
- It keeps the address jump-table for agents.
- The "slug first" SEO requirement belongs to the **published URL** (`canonical_url` / the
  CMS), which is a different layer from the corpus file. The corpus file leads with the
  address; the published URL leads with the slug. Nothing is lost.

### The date-churn rule

A date in a *draft* filename is a liability: rescheduling changes the date, which means a
rename, which breaks any reference to the file. So:

- **Draft** (`01-Drafts`): omit the date - `{address}-{type}-{slug}.{ext}`. The date lives
  in frontmatter (`target_date`), where it moves freely without a rename.
- **Published snapshot** (`02-Published`) and the live-repo artifact: add the date -
  `{address}-{type}-{slug}-{YYMMDD}.{ext}`. By then the publish date is final, so no churn.

## 7. When to deviate vs conform

- **Conform** (address-first, no date in name) for internal and knowledge corpora. This is
  the benchmark-optimal default.
- **Compose** (address + slug, plus a publish date at promote) for published editorial
  corpora. Keeps navigation, adds legibility and chronology.
- **Full custom** only when an external system dictates the filenames. Document why in the
  `description`, and accept the loss of the address jump-table and the manifest cross-check.

The ordering principle: keep the address unless an external constraint forbids it; add
legibility tokens in the descriptor; never trade away navigation for a benefit you can get
at the URL layer instead.

## 8. Worked examples

- **An editorial corpus** - `style: das-address`, `pattern_draft: {address}-{type}-{slug}.md`,
  `pattern_published: {address}-{type}-{slug}-{YYMMDD}.md`. The scaffolded example
  `01.01.01-post-you-have-a-corpus.md` is already a correct draft; it gains `-260603` only
  when promoted.
- **An open-source docs corpus** - the same composed convention, but it currently has
  slug-only files (`launch-social-260526.md`), an empty `das.config.yaml`, and no manifest. Adopting
  this means a small migration: assign addresses, write the config + `naming` block, and
  point `README.md` / `CLAUDE.md` at the config instead of the dangling memory pointer.
- **Published URL layer** - `blog.example.com/you-have-a-corpus` is governed by the CMS and
  `canonical_url`, not by the corpus naming convention. Slug-first lives here.

## 9. How to add a deviation (checklist)

1. Name the axis you need and the reason.
2. Write the `naming` block in `das.config.yaml` (`style`, pattern(s), `description`).
3. Reference it from `AGENT_CONTEXT.md` / `CLAUDE.md` - do not restate the rule there.
4. Confirm `das validate` passes for the declared style.
5. Generate filenames with `das new`.

## 10. Status: what is real today

- **Current and enforced:** the `naming` block in `das.config.yaml` (round-trips through
  `das.config.yaml`; absent block resolves to the `das-address` default). `das init` writes
  the block and accepts `--naming-style das-address|slug-date|custom`. `das validate` branches
  on `style`: `das-address` (and any corpus with no block) applies the address-first rules
  unchanged (`FILE_ADDRESS_RE`, `FOLDER_NAME_RE`, and under `--strict` the `{type}` slug and
  descriptor); `slug-date` / `custom` compile the declared patterns to a regex and check each
  non-skipped file name against them, while folders stay address-based. `das new` generates the
  filename from the declared pattern, defaulting to `pattern_draft` and selecting
  `pattern_published` under `--published [--date YYMMDD]`. The composed convention in section 6
  validates under `das-address` because the date sits inside the descriptor.
- **Proposed (not yet implemented):** only the optional `PreToolUse` Write hook (section 5
  step 5) that physically rejects a non-compliant filename at save time. The spec is updated
  (sections 4 and 5.5) and the rest of the feature is built under the project's TDD loop.
