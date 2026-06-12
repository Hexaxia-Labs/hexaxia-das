# Hexaxia DAS: Document Addressing Standard

A document organization standard and CLI tool for large, growing corpora that humans and AI agents navigate together.

Every folder and file gets a **permanent numeric address** (like an IP address for documents). Every corpus gets a **machine-readable manifest** agents load in a single read - no filesystem crawl. Unlimited hierarchy depth, a formal naming convention, and an immutable corpus schema keep the address space deterministic for people and machines alike.

The permanent-address idea is inspired by [Johnny.Decimal](https://johnnydecimal.com/); Hexaxia DAS takes it to organization scale. (See [docs/philosophy.md](docs/philosophy.md).)

---

## Features

- **Unlimited depth** - `00`, `00.01`, `00.01.01`, `00.01.01.01` - go as deep as you need
- **Permanent addresses** - once assigned, an address never changes and is never reused
- **Machine-readable manifest** - `das.manifest.yaml` maps every address in one file
- **Immutable corpus schema** - `das.config.yaml` locks the naming convention at init time
- **Agent-ready** - `agent_hint` fields on manifest nodes prime AI routing at schema-build time
- **Validator** - `das validate` checks your filesystem against the convention (CI-friendly)
- **Scaffolding** - `das new` creates spec-conformant files (with a passport stub for `.md`)

---

## Install

```bash
python3 -m venv .venv
.venv/bin/pip install -e .

# confirm the install:
.venv/bin/das --version
```

---

## Quick Start

```bash
# Initialize a corpus (--tag entries are optional, repeatable)
das init atlas-technologies --org ATL --tag ACME="Acme Corp client"

# Add nodes (parent-first)
das add 00 Admin "Company governance - legal, compliance, registrations"
das add 00.01 Business-Registration "Incorporation certificates and filings"
das add 02 Clients "One subfolder per active client engagement"
das add 02.01 ACME "Acme Corp - Springfield, IL"

# Validate your filesystem
das validate
```

For a full walkthrough, see [docs/quickstart.md](docs/quickstart.md).

---

## Commands

| Command | Description |
|---|---|
| `das init CORPUS` | Initialize a new corpus |
| `das add ADDRESS LABEL DESC` | Add a node to the manifest |
| `das new ADDRESS TYPE DESCRIPTOR` | Create a spec-conformant document file (passport stub for `.md`) |
| `das ls [ADDRESS]` | List manifest nodes |
| `das find QUERY` | Search manifest by label or description |
| `das validate` | Validate corpus naming convention compliance |

Add `--strict` to `das validate` to enforce the full v0.3 filename format, including the
required `{type}` slug. Run `das --version` to print the installed package version.

See [docs/cli-reference.md](docs/cli-reference.md) for the complete reference.

---

## Naming Convention

**Folders:** `{address}-{Title-Cased-Label}/`

```
00-Admin/
00.01-Business-Registration/
00.01.01-State-Filings/
```

**Files:** `{address}-[{TAG}-]{type}-{descriptor}.ext`

```
00.01.01-contract-articles-of-incorporation.pdf
02.01.03-ACME-contract-msa-amendment.md
```

`type` is a required slug from a controlled vocabulary (see [docs/spec.md](docs/spec.md) §5.4).
`TAG` is optional and comes from the `tags` vocabulary in `das.config.yaml`. Dates and org
prefixes do not belong in filenames - see spec §5.2.

---

## Core Rules

1. Addresses are permanent. Never renumber. Never reuse a retired address.
2. `das.config.yaml` is immutable after init. Changing it is a breaking change.
3. Retire a node by setting `deprecated: true` in the manifest - never delete the entry.
4. 4 levels of depth covers most organizations. Earn deeper levels.

---

## Documentation

| Document | Description |
|---|---|
| [docs/philosophy.md](docs/philosophy.md) | Why Hexaxia DAS exists and how it goes beyond JD |
| [docs/quickstart.md](docs/quickstart.md) | Walkthrough: build a corpus from scratch |
| [docs/concepts.md](docs/concepts.md) | Core concepts: addresses, manifest, config |
| [docs/cli-reference.md](docs/cli-reference.md) | Complete CLI reference |
| [docs/spec.md](docs/spec.md) | Full Hexaxia DAS design specification |
| [docs/passports.md](docs/passports.md) | Document Passport reference: fields, format, lifecycle |
| [docs/project-registry.md](docs/project-registry.md) | The project registry: how agents find corpora (first source of truth) |
| [docs/corpus-boundaries.md](docs/corpus-boundaries.md) | Corpus boundaries, per-corpus address reset, and the workspace layer |
| [docs/agentic-memory.md](docs/agentic-memory.md) | Using DAS as cool storage for agent memory |
| [docs/passport-formats.md](docs/passport-formats.md) | Passport placement: embedded vs sidecar, and non-Markdown documents |
| [docs/whitepapers/das-position-paper.md](docs/whitepapers/das-position-paper.md) | Position paper: the deterministic floor thesis, evidence, and FAQ |
| [CHANGELOG.md](CHANGELOG.md) | Release notes |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Development setup and contribution guidelines |

---

## Status

Hexaxia DAS is at **v0.4.0** - a working POC of the standard and CLI tool. The addressing system,
manifest schema, naming convention, and validator are stable. The following are designed but
deferred to later versions:

- Agent navigation spec
- Document Passport integration
- Federation (multi-corpus addressing)

> Three version axes travel together and are intentionally distinct: the **tool/package version**
> is `0.4.0` (this POC), the **design spec version** is `v0.3` (see [docs/spec.md](docs/spec.md)),
> and the **schema version** written into `das.config.yaml` / `das.manifest.yaml` is `"1.0"`
> (the on-disk file format). They version independently.

---

## On the word "standard"

A standard is conferred by the people who adopt it, not declared by the person who wrote it. Today DAS is an open convention and a reference CLI that I run across more than a dozen of my own corpora. It becomes a standard the day someone outside Hexaxia adopts it on theirs. If that is you, open an issue. I would rather earn the word than claim it.

---

## License

Apache 2.0 - see [LICENSE](LICENSE) for details.
