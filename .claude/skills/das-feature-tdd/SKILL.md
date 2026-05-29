---
name: das-feature-tdd
description: Use when implementing or modifying any das CLI command or module - the project's test-driven loop. Enforces failing test first (tests/test_cli.py with the corpus fixture and CliRunner), then minimal implementation in das/, then docs and changelog. Triggers on "add a command", "fix das", "implement", "change the manifest/validator/config", "new feature for the tool".
---

# das-feature-tdd

The development loop for the `das` Python tool. Rigid skill - follow the order. Tests fail
before code exists; code is minimal; docs and changelog are part of "done".

## Loop

1. **Write the failing test first** in `tests/test_cli.py`. Use the `corpus` fixture
   (a `tmp_path` with a pre-written config + empty manifest) and Typer's `CliRunner` to
   invoke commands in-process. Do not shell out. Follow the existing test patterns.
2. **Run it and confirm it fails for the right reason:**
   `.venv/bin/pytest tests/test_cli.py::<test_name> -v`
3. **Write the minimal implementation** in the right module:
   - `das/cli.py` - the Typer command (thin shim; translate errors to `typer.Exit(1)` with
     `err=True`).
   - `das/manifest.py` - address/node logic.
   - `das/config.py` - corpus header logic.
   - `das/validator.py` - corpus-walk validation rules.
   Keep logic in the data/operation modules, not in the CLI shim, so tests exercise it
   without subprocess overhead.
4. **Run the test and confirm it passes**, then run the full suite: `.venv/bin/pytest`.
5. **Update docs and changelog (required for every new CLI command):**
   - `docs/cli-reference.md` - add the command entry.
   - `CHANGELOG.md` - add a line under `## [Unreleased]`.
6. **Commit** with a `<type>: <description>` message (feat, fix, docs, test, refactor).

## Conventions (enforced by convention, not tooling)

- `from __future__ import annotations`, dataclasses, type hints.
- No third-party deps beyond `typer` / `pyyaml` (plus `pytest` for dev).
- No em dashes anywhere - use ` - ` (hyphen with spaces) or reword.
- `das.config.yaml` is immutable after init; the manifest is append-mostly (retire with
  `deprecated: true`, never delete). Changing `config.py` field semantics is spec-breaking.

Recall/store design rationale via `synapaxia-memory`. For retrieval/naming feature design,
consult `retrieval-design` first. For empirical ML validation, use `embedding-eval`.
