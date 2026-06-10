# Changelog

All notable changes to Hexaxia DAS are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.4.0] - 2026-06-10

### Changed
- Address grammar now accepts segments of **two or more digits** (variable
  segment width, spec §7.6). The validator and naming regexes were widened from
  a fixed two-digit segment (`\d{2}`) to `\d{2,}` in `das/manifest.py`
  (`ADDRESS_RE`, `FILE_ADDRESS_RE`, `FOLDER_NAME_RE`) and `das/naming.py`
  (address token). Two digits remains the default and recommended width; three
  and four digits are available for high-fan-out levels (data/research corpora,
  automated ingestion). A segment with fewer than two digits is still malformed.
  Mixing widths across levels is allowed; mixing within a single level is a
  documented convention, not tool-enforced. Tests added in `test_validator.py`.
  Brings the tool in line with `docs/address-segment-width.md` and spec §7.6.
- TAG-code grammar widened from letters-only (`^[A-Z]{2,5}$`) to
  uppercase-alphanumeric starting with a letter (`^[A-Z][A-Z0-9]{1,4}$`) in both
  the filename tag-token validator and the `das.config.yaml` tag-code check. The
  letters-only rule rejected real brand/product codes that contain digits - most
  concretely `NW7`, and predictably `M365` and `O365`.
  The leading-letter anchor keeps the three filename tokens unambiguous: an
  address segment is all digits, a tag now starts with a letter, and a type slug
  is lowercase. A purely numeric token (e.g. `868`) is still rejected as a tag.
  Changed in `das/config.py` (`TAG_CODE_RE`) and `das/naming.py`
  (`TOKEN_FRAGMENTS["TAG"]`). Tests added in `test_config.py`, `test_validator.py`,
  and `test_naming.py`. Spec §4.1, §5.3 rule 6 (with a use-case note), and §9
  rule 7 updated in `docs/spec.md`; the `tags` rule in `docs/passports.md`
  updated to match.

### Added
- `docs/passport-formats.md`: passport placement - the embedded-vs-sidecar design space, a
  survey of native metadata affordances per format family (PDF/XMP, OOXML custom properties,
  EXIF, none-for-data-files), and the standard's posture: embedded for plain-text formats,
  sidecar for everything else, plain text always the source of truth, artifact filed verbatim.
  Includes the pairing convention, integrity fields (`artifact`, `checksum`), and the open
  gaps (no pairing validation yet, sidecar RAG equivalence assumed not measured). Cross-linked
  from passports.md, corpus-layout-patterns.md, and the position paper's limits section.
- `docs/whitepapers/das-position-paper.md` finalized as the v1.0 position paper (first
  draft 2026-05-29): the deterministic-floor thesis, the UUID objection, honestly-framed
  benchmark evidence, the positioning FAQ, and the validating at-scale experiment. Linked
  from the README documentation table.
- `docs/agentic-memory.md`: using DAS as the cool-storage tier for agent memory - the
  durable, addressed system of record beneath a rebuildable warm (RAG) index, with a light
  treatment of the hot/warm/cool tiers, consolidation (only consolidated memory earns an
  address), and the clean boundary between what DAS provides (durable provenanced store) and
  what the layers above do (similarity search, recall, forgetting). Cross-links Pattern 4.
- `docs/corpus-boundaries.md`: corpus boundaries and the workspace layer - the address
  space is per-corpus and resets to `00` at every corpus root (named-root containment), and
  DAS-style numbering can be used loosely *above* corpora to organize many independent corpora
  (of different organizational types) in one workspace without merging their address spaces.
  Clarifies what the tool manages (a single corpus root) versus what is organizing convention
  (the workspace/container levels). Cross-linked from README and federation.md.
- Two type slugs added to the spec 5.4 controlled vocabulary (now 17): `email`
  (correspondence record) and `log` (time / activity / change record). Both are
  recurring client-work document intents observed in practice
  (e.g. `02.05-email-...`, `02.05-log-...`) that previously had no fitting slug
  and failed `das validate --strict`. The vocabulary remains hard-capped: it
  extends only by explicit addition. `das new` now accepts both; `das validate
  --strict` now passes files that use them. Tests added in `test_manifest.py`
  and `test_creator.py`. Spec §5.4 and the passport `type` field reference
  (now "17 type slugs") updated in `docs/spec.md` and `docs/passports.md`.

- `docs/agent-guide.md`: navigation protocol for AI agents operating in a DAS corpus - loading
  config and manifest at entry, routing via `agent_hint` fields, tag-based file discovery,
  passport-first read before acting, correct filing procedure, and what agents must not do.
  Cites benchmark findings on the rag-nav pattern and tag search.
- `docs/migration.md`: procedure for converting an existing document collection to DAS -
  assessment criteria, five-phase migration procedure (design, init, address tree, file, validate,
  record), and source-specific guidance for JD corpora, wiki exports, and flat folder structures.
- `docs/federation.md`: multi-corpus addressing model - the `ORG:address` federated reference
  format, when to federate vs. keep content in one corpus, how agents resolve cross-corpus
  references via the project registry, and how to write federated references in passports and
  agent hints.
- `docs/das-migration-convention.md`: describes the `das.migration.md` corpus root file - what
  belongs in it, what does not, the entry format (date, type, reason, address remapping table),
  where it lives, how to write a retroactive record from git history, and its relationship to
  the manifest.
- `docs/corpus-audit.md`: systematic corpus audit procedure across four layers - filesystem/naming
  (`das validate`), manifest completeness (forward and reverse), passport quality (missing passports,
  empty required fields, stale temporal validity, unverified verified_good), and convention
  compliance. Includes repair priority ordering and a report format.
- `docs/corpus-layout-patterns.md`: five corpus layout patterns with address strategies and
  passport shape additions - Editorial/Content (slug-date, lifecycle fields), Product/Corporate
  (gapped numbering, visibility/edition), Data/Research (sidecar passports, coverage matrix),
  Agent Memory (temporal validity, consolidation), and Mixed (address range separation). Includes
  a pattern-selection table and the Foundry mixed-corpus example.
- `docs/dynamic-corpus-management.md`: corpus lifecycle (Young/Active/Mature), batch filing
  procedure, when to add a new area vs. not, the promotion path (local to shared to public),
  retiring content (deprecate never delete), ETL ingestion procedure, and corpus health signals
  table.
- `docs/address-segment-width.md`: full treatment of two/three/four-digit address segments -
  slot counts, when to widen, how to mix widths across levels without mixing within a level,
  declaring width in corpus conventions, and the cost of retrofitting.
- `docs/restructuring-a-corpus.md`: guidance on top-level corpus alteration (reshaping areas or
  renaming the corpus) under permanent addresses - the young-vs-calcified decision, the rename +
  re-address procedure, and recording the reshape in `das.migration.md`. Worked example:
  Northwind-Project -> Relay. Cross-referenced from spec §6.2.
- Spec §7.5 "Numbering Strategy: Sequential vs Gapped" - guidance on area address allocation
  under permanent addresses (insertion headroom vs density) and when to use each. Records why
  `Northwind-Project` gaps its areas while the division and editorial corpora number sequentially.
- Declared per-corpus naming conventions (spec §4 `naming` block, §5.5; full design in
  `docs/corpus-conventions.md`). A corpus may declare its filename convention as one
  machine-readable source of truth:
  - `das.config.yaml` gains an optional `naming` block (`style` = `das-address` | `slug-date` |
    `custom`, plus `pattern_draft`, `pattern_published`, `description`), modeled as a typed
    `NamingConvention`. It round-trips through `load_config` / `write_config`, an absent block
    resolves to the `das-address` default (`resolve_naming`), a hand-authored YAML mapping
    hydrates into the dataclass, and empty sub-fields are omitted from the file.
  - `das init --naming-style das-address|slug-date|custom` writes the block, seeded with
    sensible patterns per style. Defaults to `das-address`; an invalid style exits 1.
  - `das validate` branches on `style`. `das-address` (and any corpus with no block) behaves
    exactly as before. `slug-date` / `custom` compile the declared patterns to a regex and
    validate each non-skipped file name against them; folders stay address-based. All existing
    skip-sets (hidden, `_`-prefix, `Zone.Identifier`, root repo files) are preserved.
  - `das new --published [--date YYMMDD]` generates the filename from the corpus's declared
    pattern: `pattern_draft` by default (dateless, since a draft date churns on reschedule),
    `pattern_published` (with the publish date) under `--published`.
  - New `das/naming.py` compiles a pattern's tokens (`{address}` `{TAG}` `{type}`
    `{descriptor}` `{slug}` `{YYMMDD}` `{ext}`, with optional `[...]` groups) to an anchored
    regex and renders concrete filenames from token values.
- `das new` creates a validated, spec-v0.3-conformant document file at an address and
  scaffolds a passport stub in `.md` files.
- Document Passport reference (docs/passports.md) and a normative passport definition in spec section 10.2 (previously deferred).
- Project registry doc (docs/project-registry.md): how agents resolve which corpus to open via
  the external `~/Projects/project-registry/` `lookup.sh`, and how that "step 0" relates to the
  manifest, federation, and the no-RAG navigation spine. Cross-linked from README and concepts.
- `das validate --strict` now also enforces a present, lowercase-hyphenated file descriptor and per-word Title-Cased folder labels (in addition to the `{type}` slug). Default validation is unchanged.

### Changed
- Spec §7.6 added: "Segment Width: Two, Three, or Four Digits" - normative guidance on when
  to use two, three, or four-digit address segments, mixing widths across levels, declaring
  width in corpus conventions, and retrofitting cost.
- Spec §6.2 cross-references updated to link `corpus-layout-patterns.md` and
  `dynamic-corpus-management.md`.
- `docs/philosophy.md` extended with two closing sections: "The Standard Is Flexible - But
  Only If You Think First" (permanence forces upfront decisions; all design parameters are
  valid if deliberate and declared) and "Many Corpora, Varying Standards" (named-root
  containment means conventions do not bleed across corpora; the standard is the floor).

### Fixed
- `write_manifest` now uses `yaml.safe_dump` (SafeDumper) instead of `yaml.dump`
  (full Dumper). `description` and `agent_hint` values containing `": "` were written
  as unquoted YAML scalars by older PyYAML versions, causing `yaml.safe_load` to raise a
  scanner error ("mapping values are not allowed here"). Switching to `safe_dump` makes
  quoting behaviour deterministic and explicit regardless of PyYAML version. Six
  regression tests added across `test_manifest.py` and `test_cli.py`.

## [0.3.0] - 2026-05-29

### Added
- `das --version` flag: prints the installed package version (`das.__version__`) and exits.
- `tags` config field (spec v0.3 section 4): optional controlled vocabulary mapping a 2-5
  uppercase code to a human description. Validated in `DASConfig.__post_init__`, round-trips
  through `load_config`/`write_config`, and is omitted from the file when unset. Populate at
  init with the repeatable `das init --tag CODE=description` option.
- `das validate` now enforces the filename tag vocabulary (spec v0.3 section 5.2/5.3 rule 6):
  when the config defines `tags`, a filename's tag (the uppercase 2-5 letter token immediately
  after the address) must be a key in that vocabulary; an unknown tag is a `ValidationError`.
  Enforcement is skipped entirely when no `tags` vocabulary is defined, so existing untagged
  corpora are unaffected. Folder names are not tag-checked.
- `das validate --strict` enforces the filename `{type}` slug against the spec 5.4 vocabulary
  (folders exempt). Default validation is unchanged.

### Changed
- Documentation reconciliation to remove drift from the source of truth. Clarified the three
  independent version axes (tool/package `0.3.0`, design spec `v0.3`, on-disk schema `"1.0"`)
  across `README.md`, `docs/concepts.md`, and `docs/quickstart.md`; bumped the stale `README.md`
  Status from `v0.1.0` to `v0.3.0`. Updated the file naming convention in `README.md`,
  `docs/concepts.md`, and `docs/quickstart.md` to the adopted spec v0.3 format
  `{address}-[{TAG}-]{type}-{descriptor}.ext` with corrected examples. Documented `das.config.yaml`
  fields as actually emitted by the CLI and flagged the spec'd-but-unimplemented `tags` field.
  Corrected `CONTRIBUTING.md` to drop the non-existent `das --version` flag, and fixed stale
  research cross-references (spec `v0.2` -> `v0.3`; corpus file count `55` -> `56`).

### Removed
- `das init` no longer writes the legacy `context_type` / `date_format` config fields, and the
  `--context-type` / `--date-format` options are removed (spec v0.3 section 4). Existing configs
  containing these keys still load - they are ignored.

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
