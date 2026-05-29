# Changelog

All notable changes to Hexaxia DAS are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Project-local Claude Code agents (`das-engineer`, `das-operator`) and an 8-skill library
  under `.claude/`, wired to synapaxia for agent memory.

### Fixed
- `das add` now rejects malformed addresses (e.g. `abc`, `5`) instead of writing them to
  the manifest.
- `das validate` now flags root-level address-bearing files whose address is not in the
  manifest (previously passed silently).

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
