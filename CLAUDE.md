# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Hexaxia DAS (Document Addressing Standard) — a Python CLI (`das`) that manages document corpora organized by permanent numeric addresses. Extends Johnny.Decimal with unlimited depth, a YAML manifest, and a corpus-level config schema. Currently v0.2.0, POC stage; spec is at v0.3 in `docs/spec.md`.

## Common Commands

Setup, test, and run all use the venv directly — do not activate it:

```bash
.venv/bin/pip install -e ".[dev]"   # install with dev deps
.venv/bin/pytest                    # run all tests
.venv/bin/pytest tests/test_cli.py -v
.venv/bin/pytest tests/test_cli.py::test_init_creates_files -v   # single test
.venv/bin/das --help                # exercise CLI
```

There is no linter or formatter configured. Dependencies are intentionally minimal — only `typer` and `pyyaml` plus `pytest` for dev.

## Architecture

Four small modules in `das/`, each owning one concern. The CLI is a thin shim — all logic lives in the data/operation modules so tests can exercise it without subprocess overhead.

- **`config.py`** — `DASConfig` dataclass + `load_config` / `write_config`. Represents `das.config.yaml`, the immutable corpus header (corpus name, org code, context_type, date format). `address_separator` is enforced to `"."` in `__post_init__`. `context_type` is constrained to `VALID_CONTEXT_TYPES`. Both loaders filter unknown YAML keys via dataclass `fields()` so older manifests stay forward-compatible.
- **`manifest.py`** — `DASManifest` / `ManifestNode` + `add_node`, `search_nodes`, `load_manifest`, `write_manifest`. Represents `das.manifest.yaml`, the address → node mapping. `infer_parent` strips the last `.NN` segment; `infer_type` maps depth to `LEVEL_TYPES = [area, category, subcategory, context]`. `add_node` enforces parent-must-exist and stamps `manifest.updated`. `write_manifest` writes nodes sorted by address and omits None/False fields to keep YAML clean.
- **`validator.py`** — `validate_corpus(corpus_root) -> List[ValidationError]`. Walks the corpus with `rglob`, applies the regex address rules (`ADDRESS_RE`, `FILE_ADDRESS_RE`, `FOLDER_NAME_RE`), and cross-checks addresses against the manifest. Has explicit skip-sets for hidden files, underscore-prefixed drafts, Windows `Zone.Identifier` ADS files, and root-level repo files (`.md`/`.sh`/`.txt`). Returns errors rather than raising — `das validate` formats them and exits non-zero.
- **`cli.py`** — `typer.Typer` app exposed as the `das` script entry point. Each command (`init`, `add`, `ls`, `find`, `validate`) loads config, loads manifest, calls into the operation modules, and translates exceptions to `typer.Exit(1)` with `err=True`. Errors from `load_config` / `load_manifest` are caught and rewritten to user-facing messages.

The two YAML files are the corpus's authoritative state — `das.config.yaml` (immutable after init) and `das.manifest.yaml` (append-mostly; retire via `deprecated: true`, never delete). Changing `config.py` field semantics is a spec-breaking change.

## Testing Pattern

`tests/conftest.py` provides a `corpus` fixture: a `tmp_path` with a pre-written config + empty manifest. CLI tests use Typer's `CliRunner` to invoke commands in-process. When adding a CLI command, follow the existing pattern in `tests/test_cli.py` and use the `corpus` fixture — do not shell out.

## Conventions

- Match the existing style: `from __future__ import annotations`, dataclasses, type hints, no third-party deps beyond `typer`/`pyyaml`.
- No em dashes in code, comments, docstrings, or docs. Use ` - ` (hyphen with spaces) or reword. This is enforced by convention, not tooling.
- Every new CLI command needs: implementation in `das/cli.py`, test in `tests/test_cli.py`, and an entry in `docs/cli-reference.md`. Update `CHANGELOG.md` under `## [Unreleased]`.
- Commit messages: `<type>: <description>` (feat, fix, docs, test, refactor).

---

## Research Context

This project has a second major component alongside the CLI: a **navigation benchmark** that measures how well agents navigate DAS corpora under different naming conventions, manifest configurations, and RAG setups. If you are asked to work on testing, findings, or the benchmark harness, read these before doing anything:

| Document | What it covers |
|---|---|
| `rag-testing-methods.md` | RAG infrastructure, chunk format, query flow, scripts, model results |
| `docs/spec.md` | The DAS spec — v0.3 includes tag guidance derived from benchmark findings |
| `docs/research/nav-test-findings-260528.md` | Full benchmark findings, 12 findings, 8 recommendations |
| `docs/research/naming-convention-analysis-260528.md` | Signal analysis per naming element, tag guidance, corpus test results |
| `docs/research/benchmark-design-260528.md` | Question taxonomy, how to interpret results, variance thresholds, open questions |
| `docs/writing-passport-summaries.md` | Practical guide to writing passport summaries for RAG quality |

### Benchmark harness location

```
~/Projects/das-nav-test/          # harness — NOT in this repo
  nav-test.py                     # main test runner
  rag-test.py                     # RAG embed + retrieval accuracy test
  report.py                       # generates RESULTS.md from run JSONs
  results/                        # 38 run JSON files
  RESULTS.md                      # generated report
```

The harness is a separate local project, not pushed to GitHub. The research docs in `docs/research/` are the committed output.

### Key benchmark findings (summary)

- **rag-nav-mxbai** is the best navigation pattern: -33% turns vs original, -25% output tokens
- **Filename tag search** (`find . -name '*-TAG-*'`) is the best discovery pattern: -56% turns
- **Folder address prefixes are not required** - DAS v3 filenames alone carry the jump-table signal
- **mxbai-embed-large** routes correctly 7/8 questions; nomic-embed-text routes 3/8
- **Passport summary quality** is the highest-leverage improvement lever for RAG accuracy
