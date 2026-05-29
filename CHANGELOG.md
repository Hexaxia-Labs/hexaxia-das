# Changelog

All notable changes to Hexaxia DAS are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- `tags` config field (spec v0.3 section 4): optional controlled vocabulary mapping a 2-5
  uppercase code to a human description. Validated in `DASConfig.__post_init__`, round-trips
  through `load_config`/`write_config`, and is omitted from the file when unset. Populate at
  init with the repeatable `das init --tag CODE=description` option.
- Project-local Claude Code agents (`das-engineer`, `das-operator`) and an 8-skill library
  under `.claude/`, wired to synapaxia for agent memory.

### Changed
- Documentation reconciliation to remove drift from the source of truth. Clarified the three
  independent version axes (tool/package `0.2.0`, design spec `v0.3`, on-disk schema `"1.0"`)
  across `README.md`, `docs/concepts.md`, and `docs/quickstart.md`; bumped the stale `README.md`
  Status from `v0.1.0` to `v0.2.0`. Updated the file naming convention in `README.md`,
  `docs/concepts.md`, and `docs/quickstart.md` to the adopted spec v0.3 format
  `{address}-[{TAG}-]{type}-{descriptor}.ext` with corrected examples. Documented `das.config.yaml`
  fields as actually emitted by the CLI and flagged the spec'd-but-unimplemented `tags` field.
  Corrected `CONTRIBUTING.md` to drop the non-existent `das --version` flag, and fixed stale
  research cross-references (spec `v0.2` -> `v0.3`; corpus file count `55` -> `56`).

### Fixed
- `das add` now rejects malformed addresses (e.g. `abc`, `5`) instead of writing them to
  the manifest.
- `das validate` now flags root-level address-bearing files whose address is not in the
  manifest (previously passed silently).
- `das validate` now reports 'invalid address format' for malformed numeric prefixes (e.g.
  `123-Weird`) instead of 'No address prefix found'.

---

## [0.1.0] - 2026-05-27

Initial release of Hexaxia DAS: Document Addressing Standard.

### Standard

- DAS addressing: dotted two-digit segments (`00`, `00.01`, `00.01.01`), unlimited depth
- Folder naming convention: `{address}-{Title-Cased-Label}/`
- File naming convention: `{address}-[{ORG}-][{CONTEXT}-]{descriptor}[-{YYMMDD}].ext`
- `das.config.yaml` schema: corpus config with `org`, `context_type`, `date_format` fields
- `das.manifest.yaml` schema: corpus map with `label`, `description`, `type`, `parent`,
  `agent_hint`, and `deprecated` fields
- Permanence rule: addresses are never renumbered or recycled
- Deprecation rule: retired nodes set `deprecated: true`, never deleted

### CLI Tool

- `das init` - initialize a corpus with config and manifest
- `das add` - add a node to the manifest (address, label, description, optional agent_hint)
- `das ls` - list manifest nodes, optionally filtered to a subtree
- `das find` - search manifest by label or description (case-insensitive substring match)
- `das validate` - validate corpus against naming convention (exits 1 if errors found)

### Tech

- Python 3.10+ required
- Dependencies: typer 0.12+, pyyaml 6.0+
- 51 tests, 0.21s test suite

### Future (deferred to v0.2+)

- Agent navigation spec
- Document Passport integration (DAS address as passport primary key)
- Federation (multi-corpus addressing with org prefix)
- `das deprecate` command for retiring nodes via CLI
- Reverse manifest validation (detect stale manifest entries for deleted folders)
