# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Hexaxia DAS (Document Addressing Standard) - a Python CLI (`das`) that manages document corpora organized by permanent numeric addresses. Extends Johnny.Decimal with unlimited depth, a YAML manifest, and a corpus-level config schema. Currently v0.4.0, POC stage; spec is at v0.3 in `docs/spec.md`.

## Common Commands

Setup, test, and run all use the venv directly - do not activate it:

```bash
.venv/bin/pip install -e ".[dev]"   # install with dev deps
.venv/bin/pytest                    # run all tests
.venv/bin/pytest tests/test_cli.py -v
.venv/bin/pytest tests/test_cli.py::test_init_creates_files -v   # single test
.venv/bin/das --help                # exercise CLI
```

There is no linter or formatter configured. Dependencies are intentionally minimal - only `typer` and `pyyaml` plus `pytest` for dev.

## Architecture

Four small modules in `das/`, each owning one concern. The CLI is a thin shim - all logic lives in the data/operation modules so tests can exercise it without subprocess overhead.

- **`config.py`** - `DASConfig` dataclass + `load_config` / `write_config`. Represents `das.config.yaml`, the immutable corpus header (corpus name, org code, tag vocabulary, declared naming convention). `address_separator` is enforced to `"."` and tag codes are validated against `TAG_CODE_RE` in `__post_init__`; the `naming` block hydrates into a typed `NamingConvention` (styles constrained to `VALID_NAMING_STYLES`). Both loaders filter unknown YAML keys via dataclass `fields()` so older configs stay forward-compatible.
- **`manifest.py`** - `DASManifest` / `ManifestNode` + `add_node`, `search_nodes`, `load_manifest`, `write_manifest`. Represents `das.manifest.yaml`, the address → node mapping. `infer_parent` strips the last `.NN` segment; `infer_type` maps depth to `LEVEL_TYPES = [area, category, subcategory, context]`. `add_node` enforces parent-must-exist and stamps `manifest.updated`. `write_manifest` writes nodes sorted by address and omits None/False fields to keep YAML clean.
- **`validator.py`** - `validate_corpus(corpus_root) -> List[ValidationError]`. Walks the corpus with `rglob`, applies the regex address rules (`ADDRESS_RE`, `FILE_ADDRESS_RE`, `FOLDER_NAME_RE`), and cross-checks addresses against the manifest. Has explicit skip-sets for hidden files, underscore-prefixed drafts, Windows `Zone.Identifier` ADS files, and root-level repo files (`.md`/`.sh`/`.txt`). Returns errors rather than raising - `das validate` formats them and exits non-zero.
- **`cli.py`** - `typer.Typer` app exposed as the `das` script entry point. Each command (`init`, `add`, `ls`, `find`, `validate`) loads config, loads manifest, calls into the operation modules, and translates exceptions to `typer.Exit(1)` with `err=True`. Errors from `load_config` / `load_manifest` are caught and rewritten to user-facing messages.

The two YAML files are the corpus's authoritative state - `das.config.yaml` (immutable after init) and `das.manifest.yaml` (append-mostly; retire via `deprecated: true`, never delete). Changing `config.py` field semantics is a spec-breaking change.

## Testing Pattern

`tests/conftest.py` provides a `corpus` fixture: a `tmp_path` with a pre-written config + empty manifest. CLI tests use Typer's `CliRunner` to invoke commands in-process. When adding a CLI command, follow the existing pattern in `tests/test_cli.py` and use the `corpus` fixture - do not shell out.

## Conventions

- Match the existing style: `from __future__ import annotations`, dataclasses, type hints, no third-party deps beyond `typer`/`pyyaml`.
- No em dashes in code, comments, docstrings, or docs. Use ` - ` (hyphen with spaces) or reword. This is enforced by convention, not tooling.
- Every new CLI command needs: implementation in `das/cli.py`, test in `tests/test_cli.py`, and an entry in `docs/cli-reference.md`. Update `CHANGELOG.md` under `## [Unreleased]`.
- Commit messages: `<type>: <description>` (feat, fix, docs, test, refactor).

