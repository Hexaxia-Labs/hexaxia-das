# Contributing to Hexaxia DAS

---

## Prerequisites

- Python 3.10 or higher
- Git

---

## Development Setup

Clone the repo and create a virtual environment:

```bash
git clone https://github.com/Hexaxia-Labs/hexaxia-das.git
cd hexaxia-das
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

Verify the install:

```bash
.venv/bin/das --help
.venv/bin/pytest
```

All 51 tests should pass.

---

## Running Tests

```bash
.venv/bin/pytest
```

With verbose output:

```bash
.venv/bin/pytest -v
```

Run a single test file:

```bash
.venv/bin/pytest tests/test_config.py -v
```

---

## Project Structure

```
hexaxia-das/
  das/
    cli.py        - typer commands (init, add, ls, find, validate)
    config.py     - DASConfig dataclass, load_config, write_config
    manifest.py   - DASManifest, ManifestNode, manifest operations
    validator.py  - validate_corpus, ValidationError
  tests/
    conftest.py   - corpus fixture (tmp_path with initialized corpus)
    test_config.py
    test_manifest.py
    test_validator.py
    test_cli.py
  docs/
    spec.md           - Hexaxia DAS design specification
    concepts.md       - core concepts reference
    quickstart.md     - walkthrough guide
    cli-reference.md  - complete command reference
```

---

## Coding Conventions

- Match the style of the existing code: dataclasses, type annotations, no magic
- No third-party deps beyond typer and pyyaml
- All new code needs tests - follow the TDD pattern in the existing test suite
- No em dashes in any written content (docs, comments, strings). Use a plain hyphen with
  spaces ( - ) or reword.

---

## Adding a Command

1. Add the command function to `das/cli.py` decorated with `@app.command()`
2. Add a test in `tests/test_cli.py` using the `corpus` fixture from `conftest.py`
3. Document the command in `docs/cli-reference.md`

The `corpus` fixture gives you a `tmp_path`-based initialized DAS corpus and a
`CliRunner` for invoking commands without a real subprocess.

---

## Pull Request Guidelines

- One feature or fix per PR
- Tests pass: `pytest` exits 0
- New commands are documented in `docs/cli-reference.md`
- Update `CHANGELOG.md` under `## [Unreleased]`
- Commit messages follow `<type>: <description>` (feat, fix, docs, test, refactor)

---

## Reporting Issues

Open an issue on GitHub. Include:
- Hexaxia DAS version (`das --version` once implemented, or the git SHA)
- Python version (`python3 --version`)
- The command you ran
- The error output
