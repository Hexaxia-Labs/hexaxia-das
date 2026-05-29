# CLI Remediation Plan

> Produced by the das-engineer agent from the 2026-05-28 project evaluation. Planning artifact; implement Tasks 1-4 first (BLOCKING + SHOULD-FIX). Tasks 5-6 are NICE-tier.

**Decisions (locked for this execution):**
- **D1:** Move the three address regexes (`ADDRESS_RE`, `FILE_ADDRESS_RE`, `FOLDER_NAME_RE`) into `das/manifest.py` (lowest-level module); `das/validator.py` imports them. Avoids a circular import and gives `add_node` a single source of truth.
- **D2:** Root-level address-bearing files are treated like root folders - their address must exist in the manifest (option a).
- **D3:** Hypothesis NOT adopted now. Tasks 1-4 stay dependency-free. Task 5 deferred.

Every task: write the failing test first, run `.venv/bin/pytest` to confirm it fails, implement the minimal change, run `.venv/bin/pytest -q` to confirm green, update `docs/cli-reference.md` / `CHANGELOG.md` where flagged, then commit.

---

## BLOCKING

### Task 1 - `das add` must validate the address format

**Problem:** `add_node` (`manifest.py:57-66`) never checks the address against the grammar; `das add abc`/`das add 5` corrupt the manifest (contradicts `docs/cli-reference.md:108`). `infer_type`/`infer_parent` silently tolerate junk.

**Files:** modify `das/manifest.py` (move regexes here; validate in `add_node`), `das/validator.py` (import regexes from `manifest`), add tests to `tests/test_manifest.py` + `tests/test_cli.py`, update `docs/cli-reference.md` + `CHANGELOG.md`.

**Failing tests** (`tests/test_cli.py`):
```python
def test_add_rejects_non_numeric_address(tmp_path):
    runner.invoke(app, ["init", "my-corpus", "--path", str(tmp_path)])
    result = runner.invoke(app, ["add", "abc", "Foo", "bar", "--path", str(tmp_path)])
    assert result.exit_code == 1
    assert "address" in result.output.lower()

def test_add_rejects_single_digit_segment(tmp_path):
    runner.invoke(app, ["init", "my-corpus", "--path", str(tmp_path)])
    result = runner.invoke(app, ["add", "5", "Foo", "bar", "--path", str(tmp_path)])
    assert result.exit_code == 1

def test_add_rejects_invalid_address_leaves_manifest_empty(tmp_path):
    runner.invoke(app, ["init", "my-corpus", "--path", str(tmp_path)])
    runner.invoke(app, ["add", "abc", "Foo", "bar", "--path", str(tmp_path)])
    from das.config import load_config
    from das.manifest import load_manifest
    config = load_config(tmp_path)
    manifest = load_manifest(tmp_path / config.manifest)
    assert manifest.nodes == {}
```
Unit (`tests/test_manifest.py`):
```python
def test_add_node_rejects_invalid_address(corpus):
    config = load_config(corpus)
    manifest = load_manifest(corpus / config.manifest)
    node = ManifestNode(label="Foo", description="bar", type="area")
    with pytest.raises(ValueError, match="[Aa]ddress format"):
        add_node(manifest, "abc", node)
```

**Implementation** - validate inside `add_node` (CLI already maps `ValueError`->exit 1 at `cli.py:92-94`, no cli.py change needed):
```python
# das/manifest.py (requires `import re`):
ADDRESS_RE = re.compile(r"^\d{2}(\.\d{2})*$")
FILE_ADDRESS_RE = re.compile(r"^(\d{2}(\.\d{2})*)-")
FOLDER_NAME_RE = re.compile(r"^\d{2}(\.\d{2})*-[A-Z][a-zA-Z0-9-]*$")

def add_node(manifest, address, node):
    if not ADDRESS_RE.match(address):
        raise ValueError(
            f"Invalid address format: '{address}' "
            "(expected two-digit segments separated by dots, e.g. '00.01')"
        )
    if address in manifest.nodes:
        raise ValueError(f"Address '{address}' already exists in manifest")
    ...
```
`das/validator.py` - replace the regex definitions (lines 10-12) with:
```python
from das.manifest import (
    load_manifest, MANIFEST_FILENAME,
    ADDRESS_RE, FILE_ADDRESS_RE, FOLDER_NAME_RE,
)
```

**Verify:** `.venv/bin/pytest -q`. Manual: `rm -rf /tmp/dt && .venv/bin/das init x --path /tmp/dt && .venv/bin/das add abc Foo bar --path /tmp/dt; echo $?` -> error + `1`.

**Regression note:** Low. Validation runs before duplicate/parent checks; existing add tests use valid addresses. Move is behavior-preserving; only `validator.py` uses these regexes internally.

**Docs/changelog:** tighten `docs/cli-reference.md` exit-code row to mention "invalid address format"; `CHANGELOG.md` `### Fixed`: "`das add` now rejects malformed addresses instead of writing them to the manifest."

**Commit:** `fix: validate address format in das add (reject non-grammar addresses)`

---

## SHOULD-FIX

### Task 2 - Cover validator skip-logic (0% tested)

**Problem:** `validator.py:55-66` skip branches (underscore prefix, `:Zone.Identifier`, root `.sh/.txt/.md`, named skips) untested.

**Files:** `tests/test_validator.py` only (no production change).

**Failing tests:**
```python
def test_underscore_prefixed_paths_are_skipped(corpus):
    (corpus / "_drafts").mkdir(); (corpus / "_drafts" / "wip.md").touch()
    (corpus / "_notes.md").touch()
    assert validate_corpus(corpus) == []

def test_zone_identifier_files_are_skipped(corpus):
    (corpus / "report.pdf:Zone.Identifier").touch()
    assert validate_corpus(corpus) == []

def test_root_repo_files_are_skipped(corpus):
    (corpus / "build.sh").touch(); (corpus / "NOTES.txt").touch(); (corpus / "README.md").touch()
    assert validate_corpus(corpus) == []

def test_named_root_skips_are_skipped(corpus):
    (corpus / "GOOGLE-DRIVE-SYNC.md").touch(); (corpus / "drive-sync.sh").touch()
    assert validate_corpus(corpus) == []

def test_root_suffix_skip_does_not_apply_in_subfolders(corpus):
    _register(corpus, "00", "Admin", "Company governance")
    (corpus / "00-Admin").mkdir(); (corpus / "00-Admin" / "loose.md").touch()
    errors = validate_corpus(corpus)
    assert any("No address prefix" in e.message for e in errors)
```
Note: if a filesystem rejects `:` in filenames on CI, adjust the Zone.Identifier test during impl.

**Verify:** `.venv/bin/pytest tests/test_validator.py -q`.

**Regression note:** None - tests only.

**Commit:** `test: cover validator skip-logic (underscore, Zone.Identifier, root files)`

---

### Task 3 - Cross-check root-level address-bearing files against the manifest

**Problem:** `validator.py:91-98` checks a file's address only against its parent folder; a root `00-orphan.md` validates clean and is never manifest-checked. (Behavior per D2 option a.)

**Files:** `das/validator.py` (file branch, lines 91-98), `tests/test_validator.py`, `docs/cli-reference.md` (validate section), `CHANGELOG.md`.

**Failing tests:**
```python
def test_root_address_file_must_be_in_manifest(corpus):
    (corpus / "00-orphan.md").touch()
    errors = validate_corpus(corpus)
    assert any("not in manifest" in e.message for e in errors)

def test_root_address_file_registered_is_valid(corpus):
    _register(corpus, "00", "Admin", "Company governance")
    (corpus / "00-orphan.md").touch()
    assert validate_corpus(corpus) == []
```

**Implementation:**
```python
if item.is_file():
    parent_address = _extract_address(item.parent.name)
    if parent_address:
        if address != parent_address:
            errors.append(ValidationError(
                str(rel),
                f"File address '{address}' does not match "
                f"parent folder address '{parent_address}'",
            ))
    else:
        if address not in manifest.nodes:
            errors.append(ValidationError(str(rel), f"Address '{address}' not in manifest"))
```

**Verify:** `.venv/bin/pytest tests/test_validator.py -q`.

**Regression note:** Medium - only task that changes validator output. Existing file tests sit under address folders (truthy `parent_address`), so the new `else` is not taken; no current fixture places an address-file at corpus root.

**Docs/changelog:** add validate-section bullet; `CHANGELOG.md` `### Fixed`: "`das validate` now flags root-level address-bearing files whose address is not in the manifest."

**Commit:** `fix: cross-check root-level address-bearing files against the manifest`

---

### Task 4 - Distinguish "malformed prefix" from "no prefix"

**Problem:** `123-Weird` reports "No address prefix found" (`validator.py:71`) though a malformed prefix is present.

**Files:** `das/manifest.py` (add `LOOSE_PREFIX_RE` with the other regexes), `das/validator.py` (branch on it), `tests/test_validator.py`, `CHANGELOG.md`.

**Failing tests:**
```python
def test_malformed_prefix_reports_invalid_format(corpus):
    (corpus / "123-Weird").mkdir()
    errors = validate_corpus(corpus)
    assert any("invalid address format" in e.message.lower() for e in errors)
    assert not any("No address prefix" in e.message for e in errors)

def test_truly_unprefixed_still_reports_no_prefix(corpus):
    (corpus / "JustText").mkdir()
    errors = validate_corpus(corpus)
    assert any("No address prefix" in e.message for e in errors)
```

**Implementation:**
```python
# das/manifest.py:
LOOSE_PREFIX_RE = re.compile(r"^\d+([.\d]*)-")  # any digit run + dash

# das/validator.py:
address = _extract_address(item.name)
if address is None:
    if LOOSE_PREFIX_RE.match(item.name):
        errors.append(ValidationError(str(rel), "Invalid address format (malformed numeric prefix)"))
    else:
        errors.append(ValidationError(str(rel), "No address prefix found"))
    continue
```

**Verify:** `.venv/bin/pytest tests/test_validator.py -q`.

**Regression note:** Low-medium. Existing "No address prefix" assertions use non-digit names (`Admin`) - unaffected. `123-Weird` still yields exactly one error, so error-count tests are unaffected.

**Docs/changelog:** `CHANGELOG.md` `### Fixed`: "`das validate` now reports 'invalid address format' for malformed numeric prefixes instead of 'No address prefix found'."

**Commit:** `fix: distinguish malformed address prefix from missing prefix in validator`

---

## NICE (deferred this pass)

### Task 5 - Hypothesis property tests for the address grammar (needs dep sign-off; D3 = no for now)
New `tests/test_grammar_properties.py` + `hypothesis` in `pyproject.toml` dev extras. Invariants: generated valid addresses match `ADDRESS_RE`; `infer_parent(addr)` is a strict prefix; non-numeric strings rejected. Deferred - adds a dependency.

### Task 6 - Populated-corpus fixture + CLI-contract tests
`populated_corpus` fixture in `conftest.py`; CLI-contract tests for uninitialized-dir errors (add/ls/find), `agent_hint` round-trip, forward-compat unknown-key loading, `[deprecated]` suffix rendering. Tests/fixtures only; safe to add anytime.

**Commit:** `test: add populated-corpus fixture and CLI-contract tests`

---

## Commit sequence
1. `fix: validate address format in das add ...` (Task 1, includes the D1 regex move)
2. `test: cover validator skip-logic ...` (Task 2)
3. `fix: cross-check root-level address-bearing files ...` (Task 3)
4. `fix: distinguish malformed address prefix ...` (Task 4)
5. *(deferred)* Task 5 - only if Hypothesis is approved
6. `test: add populated-corpus fixture and CLI-contract tests` (Task 6)
