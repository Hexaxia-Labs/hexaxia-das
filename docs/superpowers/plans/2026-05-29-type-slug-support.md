# {type}-slug Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align `das init`'s config to spec v0.3 (drop `context_type`/`date_format`) and add opt-in `das validate --strict` enforcement of the filename `{type}` slug against the 15-type vocabulary.

**Architecture:** Three independent changes. (1) Add a `VALID_TYPE_SLUGS` constant to `das/manifest.py`. (2) Remove the two legacy config fields from `DASConfig` and the `init` command. (3) Add a `strict` parameter to `validate_corpus` and a `--strict` flag to `das validate` that enforces the type slug on files; default behavior is unchanged so legacy corpora never newly-fail.

**Tech Stack:** Python 3, `typer`, `pyyaml`, `pytest`. Run via `.venv/bin/das` and `.venv/bin/pytest`. No new dependencies.

**Spec:** `docs/superpowers/specs/2026-05-29-type-slug-support-design.md`.

**Grounding facts (verified against current code on branch `feat/type-slug-support`):**
- `das/config.py`: `DASConfig` currently has `context_type`/`date_format` fields, `VALID_CONTEXT_TYPES`, and a `context_type` check in `__post_init__`. `load_config` filters unknown YAML keys via `fields()`. `write_config` omits `None` values. `TAG_CODE_RE = re.compile(r"^[A-Z]{2,5}$")` lives here.
- `das/cli.py`: `init` has `--context-type` and `--date-format` options (lines ~25-28) passed into `DASConfig` (lines ~67-68). `validate` currently takes only `path`.
- `das/manifest.py`: holds `ADDRESS_RE`, `FILE_ADDRESS_RE`, `FOLDER_NAME_RE`, `LOOSE_PREFIX_RE`, and an UNRELATED `VALID_TYPES` (manifest node levels: area/category/subcategory/file). Do NOT touch `VALID_TYPES`; the new constant is `VALID_TYPE_SLUGS` (filename types) - distinct name on purpose.
- `das/validator.py`: `validate_corpus(corpus_root)` loads config + manifest, walks `rglob`, has `_extract_address` and `_extract_tag` helpers, and a file branch with tag enforcement gated on `config.tags`.
- `tests/conftest.py`: the `corpus` fixture builds a `DASConfig` that sets `context_type="client"` and `date_format="YYMMDD"` (lines 15-16) - these MUST be removed when the fields go.
- `tests/test_config.py`: `test_optional_fields_omitted_from_file` asserts `"context_type" not in raw` (line 44); `test_invalid_context_type` (lines 58-67) tests the validation being removed.
- `tests/test_validator.py`: has helpers `_register(corpus, address, label, description, parent=None)` and `_set_tags(corpus, {...})` (added in prior work) - reuse them.
- 15 type slugs (spec 5.4): runbook, plan, spec, design, strategy, playbook, proposal, contract, report, catalog, lead, post, template, reference, procedure.

---

## File Structure

```
das/manifest.py    - add VALID_TYPE_SLUGS constant (Task 1)
das/config.py      - remove context_type/date_format fields, VALID_CONTEXT_TYPES, the check (Task 2)
das/cli.py         - remove init's two options (Task 2); add validate --strict (Task 3)
das/validator.py   - add _extract_type + strict param + strict type check (Task 3)
tests/conftest.py  - drop the two legacy fields from the corpus fixture (Task 2)
tests/test_config.py    - remove/adjust legacy-field tests, add forward-compat test (Task 2)
tests/test_cli.py       - init-option-removed test (Task 2); validate --strict test (Task 3)
tests/test_manifest.py  - VALID_TYPE_SLUGS content test (Task 1)
tests/test_validator.py - strict type-enforcement tests (Task 3)
docs/cli-reference.md, docs/concepts.md, CHANGELOG.md - per task
```

Build order: Task 1 (constant, dependency for Task 3) -> Task 2 (config alignment) -> Task 3 (strict validation).

---

### Task 1: Add the `VALID_TYPE_SLUGS` constant

**Files:**
- Modify: `das/manifest.py` (after `LOOSE_PREFIX_RE`, ~line 20)
- Test: `tests/test_manifest.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_manifest.py` (adjust the existing `from das.manifest import ...` line to include `VALID_TYPE_SLUGS`, or add a new import):

```python
def test_valid_type_slugs_are_the_spec_5_4_vocabulary():
    from das.manifest import VALID_TYPE_SLUGS
    assert VALID_TYPE_SLUGS == {
        "runbook", "plan", "spec", "design", "strategy", "playbook",
        "proposal", "contract", "report", "catalog", "lead", "post",
        "template", "reference", "procedure",
    }
    assert len(VALID_TYPE_SLUGS) == 15
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_manifest.py::test_valid_type_slugs_are_the_spec_5_4_vocabulary -v`
Expected: FAIL with `ImportError: cannot import name 'VALID_TYPE_SLUGS'`.

- [ ] **Step 3: Add the constant**

In `das/manifest.py`, immediately after the `LOOSE_PREFIX_RE = ...` line:

```python
# Filename {type} slugs - the hard-capped controlled vocabulary from spec 5.4.
# Distinct from VALID_TYPES above (which are manifest node levels).
VALID_TYPE_SLUGS = frozenset({
    "runbook", "plan", "spec", "design", "strategy", "playbook", "proposal",
    "contract", "report", "catalog", "lead", "post", "template", "reference",
    "procedure",
})
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_manifest.py -q`
Expected: PASS (all manifest tests green).

- [ ] **Step 5: Commit**

```bash
git add das/manifest.py tests/test_manifest.py
git commit -m "feat: add VALID_TYPE_SLUGS vocabulary constant (spec 5.4)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Remove `context_type`/`date_format` from config and `das init`

This is a single cohesive change: removing the fields breaks the `corpus` fixture and two tests, so the production change, the fixture, and the tests must move together in one commit.

**Files:**
- Modify: `das/config.py` (remove fields, `VALID_CONTEXT_TYPES`, the check)
- Modify: `das/cli.py` (remove the two `init` options + kwargs)
- Modify: `tests/conftest.py` (remove the two fixture lines)
- Modify: `tests/test_config.py` (remove/adjust legacy tests, add forward-compat test)
- Modify: `tests/test_cli.py` (assert the option is gone)
- Modify: `docs/cli-reference.md`, `docs/concepts.md`, `CHANGELOG.md`

- [ ] **Step 1: Write the failing tests**

In `tests/test_config.py`, ADD these two tests:

```python
def test_dasconfig_has_no_legacy_fields():
    cfg = DASConfig(
        version="1.0",
        corpus="x",
        initialized="2026-05-29",
        address_separator=".",
        manifest="das.manifest.yaml",
    )
    assert not hasattr(cfg, "context_type")
    assert not hasattr(cfg, "date_format")


def test_legacy_config_with_dropped_fields_still_loads(tmp_path):
    import yaml
    (tmp_path / "das.config.yaml").write_text(yaml.safe_dump({
        "version": "1.0",
        "corpus": "x",
        "initialized": "2026-05-29",
        "address_separator": ".",
        "manifest": "das.manifest.yaml",
        "context_type": "client",
        "date_format": "YYMMDD",
    }))
    cfg = load_config(tmp_path)
    assert cfg.corpus == "x"
    assert not hasattr(cfg, "context_type")
```

In `tests/test_cli.py`, ADD:

```python
def test_init_rejects_removed_context_type_option(tmp_path):
    result = runner.invoke(
        app, ["init", "c", "--context-type", "client", "--path", str(tmp_path)]
    )
    assert result.exit_code != 0  # Typer exit code 2: no such option
```

- [ ] **Step 2: Run the new tests to verify they fail**

Run: `.venv/bin/pytest tests/test_config.py::test_dasconfig_has_no_legacy_fields tests/test_cli.py::test_init_rejects_removed_context_type_option -v`
Expected: both FAIL - `test_dasconfig_has_no_legacy_fields` fails because the attribute still exists; `test_init_rejects_removed_context_type_option` fails because the option still works (exit 0).

- [ ] **Step 3: Remove the fields from `das/config.py`**

Delete the `VALID_CONTEXT_TYPES` line (line 10). In `DASConfig`, delete the `context_type` and `date_format` field lines. In `__post_init__`, delete the `context_type` validation block. The result:

```python
CONFIG_FILENAME = "das.config.yaml"
SPEC_VERSION = "1.0"
TAG_CODE_RE = re.compile(r"^[A-Z]{2,5}$")


@dataclass
class DASConfig:
    version: str
    corpus: str
    initialized: str
    address_separator: str
    manifest: str
    org: Optional[str] = None
    tags: Optional[dict[str, str]] = None

    def __post_init__(self):
        if self.address_separator != ".":
            raise ValueError("address_separator must be '.'")
        if self.tags:
            for code, description in self.tags.items():
                if not TAG_CODE_RE.match(code):
                    raise ValueError(
                        f"tags code '{code}' must be 2-5 uppercase letters"
                    )
                if not isinstance(description, str) or not description.strip():
                    raise ValueError(
                        f"tags code '{code}' must have a non-empty description"
                    )
```

(`load_config` and `write_config` are unchanged - the `fields()` filter now drops `context_type`/`date_format` from older files automatically.)

- [ ] **Step 4: Remove the options from `das/cli.py` `init`**

Delete the `context_type` and `date_format` `typer.Option(...)` parameters from the `init` signature (lines ~25-28), and delete `context_type=context_type,` and `date_format=date_format,` from the `DASConfig(...)` call (lines ~67-68). Leave `org`, `--tag`, and `path` intact. The `DASConfig(...)` call becomes:

```python
        config = DASConfig(
            version=SPEC_VERSION,
            corpus=corpus,
            initialized=str(date.today()),
            address_separator=".",
            manifest=MANIFEST_FILENAME,
            org=org,
            tags=tags,
        )
```

- [ ] **Step 5: Fix the `corpus` fixture in `tests/conftest.py`**

Delete the two lines `context_type="client",` and `date_format="YYMMDD",` from the `DASConfig(...)` call in the `corpus` fixture (lines 15-16). The fixture config keeps `org="TST"`.

- [ ] **Step 6: Adjust the existing legacy tests in `tests/test_config.py`**

- Delete `test_invalid_context_type` entirely (lines 58-67 in the current file).
- In `test_optional_fields_omitted_from_file`, replace the line `assert "context_type" not in raw` with `assert "tags" not in raw` (keep `assert "org" not in raw`).

- [ ] **Step 7: Run the full suite**

Run: `.venv/bin/pytest -q`
Expected: PASS. The two new tests pass; the deleted/adjusted tests no longer reference removed fields; the fixture builds without the removed kwargs.

- [ ] **Step 8: Update docs and changelog**

- `docs/cli-reference.md`: in the `das init` section, remove the `--context-type` and `--date-format` option rows/mentions. Keep `--org`, `--tag`.
- `docs/concepts.md`: in the `das.config.yaml` field table, remove the `context_type` and `date_format` rows. (Leave `org`, `tags`, `version`, etc.)
- `CHANGELOG.md`, under `## [Unreleased]`, add a `### Removed` section (or append if one exists): "`das init` no longer writes the legacy `context_type` / `date_format` config fields, and the `--context-type` / `--date-format` options are removed (spec v0.3 section 4). Existing configs containing these keys still load - they are ignored."

- [ ] **Step 9: Commit**

```bash
git add das/config.py das/cli.py tests/conftest.py tests/test_config.py tests/test_cli.py docs/cli-reference.md docs/concepts.md CHANGELOG.md
git commit -m "feat: drop legacy context_type/date_format from config and das init

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: `das validate --strict` type-slug enforcement

**Files:**
- Modify: `das/validator.py` (add `_extract_type`, `strict` param, strict check; import `VALID_TYPE_SLUGS`)
- Modify: `das/cli.py` (add `--strict` to `validate`)
- Test: `tests/test_validator.py`, `tests/test_cli.py`
- Modify: `docs/cli-reference.md`, `docs/concepts.md`, `CHANGELOG.md`

- [ ] **Step 1: Write the failing tests**

In `tests/test_validator.py` (reuse the existing `_register` and `_set_tags` helpers and the `corpus` fixture):

```python
def test_default_mode_does_not_enforce_type(corpus):
    _register(corpus, "00", "Admin", "gov")
    (corpus / "00-Admin").mkdir()
    (corpus / "00-Admin" / "00-frobnicate-foo.md").touch()
    errors = validate_corpus(corpus)  # default strict=False
    assert not any("type slug" in e.message for e in errors)


def test_strict_valid_type_slug_passes(corpus):
    _register(corpus, "00", "Admin", "gov")
    (corpus / "00-Admin").mkdir()
    (corpus / "00-Admin" / "00-reference-company-profile.md").touch()
    errors = validate_corpus(corpus, strict=True)
    assert not any("type slug" in e.message for e in errors)


def test_strict_invalid_type_slug_errors(corpus):
    _register(corpus, "00", "Admin", "gov")
    (corpus / "00-Admin").mkdir()
    (corpus / "00-Admin" / "00-frobnicate-foo.md").touch()
    errors = validate_corpus(corpus, strict=True)
    assert any("type slug 'frobnicate'" in e.message for e in errors)


def test_strict_missing_type_errors(corpus):
    _register(corpus, "00", "Admin", "gov")
    (corpus / "00-Admin").mkdir()
    (corpus / "00-Admin" / "00-orphan.md").touch()  # 'orphan' is not a type
    errors = validate_corpus(corpus, strict=True)
    assert any("type slug" in e.message for e in errors)


def test_strict_tag_then_type_passes(corpus):
    _set_tags(corpus, {"ULS": "United Life Services"})
    _register(corpus, "00", "Admin", "gov")
    (corpus / "00-Admin").mkdir()
    (corpus / "00-Admin" / "00-ULS-runbook-foo.md").touch()
    errors = validate_corpus(corpus, strict=True)
    assert not any("type slug" in e.message for e in errors)


def test_strict_folder_is_not_type_checked(corpus):
    _register(corpus, "00", "Admin", "gov")
    (corpus / "00-Admin").mkdir()  # a folder, no type slug
    errors = validate_corpus(corpus, strict=True)
    assert not any("type slug" in e.message for e in errors)
```

In `tests/test_cli.py`:

```python
def test_validate_strict_flags_bad_type(tmp_path):
    runner.invoke(app, ["init", "c", "--path", str(tmp_path)])
    runner.invoke(app, ["add", "00", "Admin", "gov", "--path", str(tmp_path)])
    (tmp_path / "00-Admin").mkdir()
    (tmp_path / "00-Admin" / "00-frobnicate-foo.md").touch()
    clean = runner.invoke(app, ["validate", "--path", str(tmp_path)])
    assert clean.exit_code == 0  # default mode ignores type
    strict = runner.invoke(app, ["validate", "--strict", "--path", str(tmp_path)])
    assert strict.exit_code == 1
    assert "type slug" in strict.output
```

- [ ] **Step 2: Run the new tests to verify they fail**

Run: `.venv/bin/pytest tests/test_validator.py -k "strict or type" tests/test_cli.py::test_validate_strict_flags_bad_type -v`
Expected: the strict-enforcement tests FAIL - `validate_corpus` does not accept `strict=` (TypeError) and `--strict` is an unknown option (exit 2). `test_default_mode_does_not_enforce_type` may already pass (no type check exists), which is fine.

- [ ] **Step 3: Add `_extract_type` and the strict check in `das/validator.py`**

Update the manifest import to include `VALID_TYPE_SLUGS`:

```python
from das.manifest import (
    load_manifest, MANIFEST_FILENAME,
    ADDRESS_RE, FILE_ADDRESS_RE, FOLDER_NAME_RE, LOOSE_PREFIX_RE,
    VALID_TYPE_SLUGS,
)
```

Add this helper next to `_extract_tag`:

```python
def _extract_type(name: str, address: str) -> Optional[str]:
    # Per spec 5.2: {address}-[{TAG}-]{type}-{descriptor}.ext. The {type} is the
    # first '-'-delimited token after the address, or the second when a TAG (an
    # uppercase 2-5 first token) is present. Returns the candidate with any file
    # extension stripped, or None if there is no candidate.
    remainder = name[len(address) + 1:]  # drop the address and its trailing '-'
    tokens = remainder.split("-")
    if not tokens or not tokens[0]:
        return None
    idx = 1 if TAG_CODE_RE.match(tokens[0]) else 0
    if idx >= len(tokens):
        return None
    candidate = tokens[idx]
    if "." in candidate:  # strip a trailing file extension on the type token
        candidate = candidate.rsplit(".", 1)[0]
    return candidate or None
```

Change the function signature:

```python
def validate_corpus(corpus_root: Path, strict: bool = False) -> List[ValidationError]:
```

Inside the `if item.is_file():` branch, AFTER the existing tag-enforcement block, add:

```python
            # Strict mode enforces the required {type} slug (spec 5.2 / 5.4).
            # Off by default so legacy corpora are not newly-failed.
            if strict:
                type_slug = _extract_type(item.name, address)
                if type_slug not in VALID_TYPE_SLUGS:
                    shown = type_slug if type_slug is not None else ""
                    errors.append(ValidationError(
                        str(rel),
                        f"Invalid or missing type slug '{shown}' "
                        "(not in the spec 5.4 vocabulary)",
                    ))
```

- [ ] **Step 4: Add the `--strict` flag to `das validate` in `das/cli.py`**

Replace the `validate` command signature and the `validate_corpus` call:

```python
@app.command()
def validate(
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Enforce the full v0.3 filename format, including the {type} slug",
    ),
    path: Path = typer.Option(Path("."), help="Corpus root directory"),
):
    """Validate corpus naming convention compliance."""
    try:
        errors = validate_corpus(path, strict=strict)
    except FileNotFoundError:
        typer.echo(f"Error: no DAS corpus found at {path}. Run 'das init' first.", err=True)
        raise typer.Exit(1)
```

(Leave the rest of the `validate` body - the error formatting and exit - unchanged.)

- [ ] **Step 5: Run the full suite**

Run: `.venv/bin/pytest -q`
Expected: PASS (all prior tests + the new strict tests).

- [ ] **Step 6: Update docs and changelog**

- `docs/cli-reference.md`: in the `das validate` section, document the `--strict` flag - "Enforces the full v0.3 filename format, including a valid `{type}` slug from the spec 5.4 vocabulary; a missing or unknown type is an error. Default validation does not check the type slug."
- `docs/concepts.md`: add a sentence to the validation discussion noting that `das validate --strict` enforces the `{type}` slug (default mode does not, for backward compatibility).
- `CHANGELOG.md`, under `## [Unreleased]` `### Added`: "`das validate --strict` enforces the filename `{type}` slug against the spec 5.4 vocabulary (folders exempt). Default validation is unchanged."

- [ ] **Step 7: Commit**

```bash
git add das/validator.py das/cli.py tests/test_validator.py tests/test_cli.py docs/cli-reference.md docs/concepts.md CHANGELOG.md
git commit -m "feat: add das validate --strict for {type}-slug enforcement

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Self-Review

**Spec coverage:**
- Part 1 (config alignment, remove context_type/date_format + options, backward-compat): Task 2. ✓
- Part 2 (VALID_TYPE_SLUGS constant in manifest.py): Task 1. ✓
- Part 3 (--strict flag, superset, type extraction reusing tag logic, folders exempt, default unchanged): Task 3. ✓
- Locked decisions: options removed not deprecated (Task 2 Step 4) ✓; constant in manifest.py (Task 1) ✓; opt-in --strict, tags stay default-on (Task 3 - the tag block is untouched, the strict block is additive) ✓.
- Non-goals (descriptor/folder-label enforcement, `das new`, version bump, removing `org`): not present in any task. ✓
- Testing section of spec: covered by Task 1 (constant), Task 2 (config + forward-compat + option-removed), Task 3 (default/strict/valid/invalid/missing/tag+type/folder). ✓
- Docs/changelog: each task has its doc + changelog step. ✓

**Placeholder scan:** No TBD/TODO. Every code step shows complete code; every test step shows real assertions; every command has expected output. No "similar to" references. ✓

**Type/name consistency:** `VALID_TYPE_SLUGS` (new, manifest.py) is distinct from the existing `VALID_TYPES` (manifest node levels) - flagged explicitly so the implementer does not conflate them. `_extract_type` mirrors the existing `_extract_tag` signature `(name, address)`. `validate_corpus(corpus_root, strict=False)` - the `strict` kwarg name is used identically in cli.py (`validate_corpus(path, strict=strict)`) and all tests (`validate_corpus(corpus, strict=True)`). `TAG_CODE_RE` is imported in validator.py already (used by `_extract_tag`) so `_extract_type` can use it without a new import. ✓
