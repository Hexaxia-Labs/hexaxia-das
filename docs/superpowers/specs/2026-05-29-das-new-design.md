# `das new` Command Design

**Date:** 2026-05-29
**Author:** Aaron Lamb (with Claude)
**Status:** Approved design - pending implementation plan

A `das new` command that creates a correctly-named document file at a DAS address,
validating the name against the spec at creation time and scaffolding a passport stub.
This is the file-creation half of the spec v0.3 type model (the validation half shipped
as `das validate --strict`).

---

## Goals

1. Make it easy to create a spec-v0.3-conformant file without hand-constructing the
   `{address}-[{TAG}-]{type}-{descriptor}.ext` name.
2. Enforce correctness at creation: valid type slug, valid tag (against the corpus
   vocabulary), valid address resolving to exactly one folder, well-formed descriptor.
3. Scaffold a passport stub in `.md` files so the highest-leverage hygiene (a passport
   summary) is present from the start.

## Non-Goals

- Editing or moving existing files, or a `das rename`/migration command.
- Writing to `das.manifest.yaml`. Files are not manifest nodes; only addresses/folders
  are. `das new` creates a file in an existing address folder and does not touch the
  manifest.
- Generating the passport `summary` content (only an empty stub field with a reminder).
- Updating the operator `corpus-ingest` skill to call `das new` (a noted follow-up).
- Creating the address folder if it does not exist (the folder must already exist).

## Locked Decisions

- **File placement:** resolve the address to its folder by scanning the corpus for the
  directory whose name starts with `{address}-`. Zero matches or more than one is an error.
- **Passport:** always scaffold a stub for `.md` files; non-`.md` files get the bare named
  file plus a warning that the passport must be tracked elsewhere.
- **Bad descriptor:** error (do not silently normalize), consistent with the tool's
  force-the-decision philosophy.
- **Module:** new `das/creator.py` holds the logic; `cli.py` is a thin shim.

---

## Command

```
das new <address> <type> <descriptor> [--tag CODE] [--ext md] [--path .]
```

| Argument/Option | Required | Description |
|---|---|---|
| `address` | Yes | DAS address, e.g. `02.01.04`. Must match `ADDRESS_RE` and resolve to one folder. |
| `type` | Yes | Type slug; must be in `VALID_TYPE_SLUGS` (spec 5.4). |
| `descriptor` | Yes | Lowercase-hyphenated slug, e.g. `netbird-ztna`. |
| `--tag CODE` | No | Tag code; requires a `tags` vocabulary in config and must be a member. |
| `--ext` | No | File extension (default `md`); lowercased. |
| `--path` | No | Corpus root directory (default `.`). |

---

## Architecture

`das/creator.py` exposes:

```python
def create_document(
    corpus_root: Path,
    address: str,
    type_slug: str,
    descriptor: str,
    tag: Optional[str] = None,
    ext: str = "md",
) -> Path:
    ...
```

It validates, resolves the folder, writes the file, and returns the created path. It
raises `ValueError` with a clear message on any failure. `das/cli.py` adds a `new` command
that calls it inside `try/except ValueError` and translates failures to `typer.Exit(1)`
with `err=True` (the existing CLI error pattern), then echoes the created relative path.

Reuses, no redefinition:
- `ADDRESS_RE`, `VALID_TYPE_SLUGS`, `_extract_address`-equivalent logic from `das.manifest`
  (import `ADDRESS_RE`, `VALID_TYPE_SLUGS`; for folder-name address extraction, reuse
  `FILE_ADDRESS_RE` via a small local check or import the validator helper - the
  implementation plan picks the cleanest non-circular option).
- `TAG_CODE_RE`, `load_config` from `das.config` (for the `tags` vocabulary).

---

## Validation Rules (all raise `ValueError`)

1. **Address format:** `address` must match `ADDRESS_RE` (`^\d{2}(\.\d{2})*$`).
2. **Type:** `type_slug` must be in `VALID_TYPE_SLUGS`; error lists the valid vocabulary.
3. **Descriptor:** must match `^[a-z0-9]+(-[a-z0-9]+)*$` (lowercase, digits, single
   hyphens; no spaces/underscores/uppercase). Error explains the rule.
4. **Tag:** if `tag` is given, `load_config(corpus_root).tags` must be defined and contain
   `tag`. If no vocabulary is defined -> error "no tags vocabulary defined in
   das.config.yaml". If defined but `tag` absent -> error "unknown tag 'X'".
5. **Folder resolution:** find directories under `corpus_root` whose name starts with
   `{address}-` and whose extracted address equals `address`. Zero -> error "no folder
   found for address 'X'". More than one -> error "ambiguous: multiple folders for
   address 'X'".
6. **No overwrite:** the target path must not already exist -> error "file already exists".
7. **Extension:** lowercase the provided `ext`; strip a leading dot if the user passed
   `.md`.

Order: cheap/local checks (address, type, descriptor) first; then config-dependent (tag);
then filesystem (folder resolution, existence).

---

## File Output

**Filename:** `{address}-[{TAG}-]{type}-{descriptor}.{ext}` (TAG segment present only when
`--tag` given). Placed inside the resolved folder.

**`.md` content (passport stub):**

```markdown
<!--
passport:
  title: "<Descriptor Titleized>"
  type: <type_slug>
  status: draft
  tags: [<tag>]
  das_address: "<address>"
  created: "<YYYY-MM-DD today>"
  summary: ""
-->

# <Descriptor Titleized>
```

- The `tags:` line is included only when `--tag` is given.
- `<Descriptor Titleized>` is the descriptor with hyphens replaced by spaces and each word
  capitalized (e.g. `netbird-ztna` -> `Netbird Ztna`). It is a placeholder for the author.
- The `summary` field is intentionally empty (`summary: ""`). No reminder is embedded
  inside the YAML (which would keep it clean and parseable); instead the command's stdout
  reminds the author to write the summary.
- `created` is today's date (`date.today()`).

**Non-`.md`:** create the empty named file and print a warning to stderr: "Created
<path>. Note: <ext> files cannot embed a passport block - record its passport separately."

**Stdout on success (.md):** "Created <relative path>. Write the passport summary - it is
the entire RAG signal."

---

## Data Flow

```
das new 02.01.04 runbook netbird-ztna --tag ULS
  -> create_document(root, "02.01.04", "runbook", "netbird-ztna", tag="ULS", ext="md")
       validate address / type / descriptor
       load_config -> tags vocabulary -> validate ULS
       resolve "02.01.04" -> exactly one folder (e.g. .../02.01.04-Projects/)
       build name 02.01.04-ULS-runbook-netbird-ztna.md ; assert not exists
       write passport-stub .md
       return path
  -> cli echoes the path (+ summary reminder)
```

A file produced by `das new` must pass `das validate --strict` (integration-tested).

---

## Error Handling

All validation failures are `ValueError` from `create_document`, surfaced by the CLI as
`Error: <message>` on stderr with exit code 1. A missing corpus config (`load_config`
raising `FileNotFoundError`, only reached when `--tag` is used) is translated to the
standard "no DAS corpus found" message. Folder-resolution and file-exists errors are
`ValueError` like the rest.

---

## Testing

**Unit (`tests/test_creator.py`, using a populated `tmp_path` corpus):**
- Happy path: creates `{address}-{type}-{descriptor}.md` in the resolved folder; returns
  the path; file contains a parseable passport block with the right `type`, `das_address`,
  `status: draft`, and an empty `summary`; no `tags:` line when no tag.
- With `--tag`: filename includes the tag; passport `tags: [CODE]` present; tag validated
  against the config vocabulary.
- Invalid type -> ValueError (message lists vocabulary).
- Unknown tag / no-vocabulary-defined -> ValueError.
- Bad descriptor (`Net Bird`, `net_bird`, `NetBird`) -> ValueError.
- Address with no folder -> ValueError; address with two matching folders -> ValueError.
- Existing target file -> ValueError (no overwrite).
- Non-`.md` ext -> bare file created, no passport block, warning behavior.

**CLI (`tests/test_cli.py`, `CliRunner`):**
- `das new` happy path: exit 0, prints the created path, file exists.
- Invalid type / unknown tag / bad descriptor / unresolved address -> exit 1 with message.

**Integration:** create a file via `das new` in a registered folder, then
`validate_corpus(root, strict=True)` returns no errors for it.

---

## Docs / Changelog

- `docs/cli-reference.md`: a `das new` section (synopsis, arguments, examples, exit codes).
- `docs/concepts.md`: optional one-line mention that `das new` scaffolds conformant files.
- `CHANGELOG.md`: `### Added` under `## [Unreleased]`.

---

## Build Order (high level)

1. `das/creator.py` `create_document` with validation + folder resolution + filename build
   (TDD, unit tests in `tests/test_creator.py`).
2. Passport-stub writing for `.md` and bare-file + warning for non-`.md`.
3. `das new` CLI command wiring (`tests/test_cli.py`) + the `--strict` integration test.
4. Docs + changelog.

Exact test code, the titleize helper, and the folder-resolution helper belong in the plan.
