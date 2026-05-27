# JDX: Johnny Decimal Extended

A document organization standard and CLI tool for large, growing corpora.

Every folder and file gets a **permanent numeric address** (like an IP address for documents).
Every corpus gets a **machine-readable manifest** that agents can load in a single read.
Humans and AI agents navigate the same address space.

JDX extends [Johnny.Decimal](https://johnnydecimal.com/) with unlimited hierarchy depth,
a formal naming convention, and a corpus-level schema - built for organizations where JD's
two-level limit becomes a ceiling.

---

## Features

- **Unlimited depth** - `00`, `00.01`, `00.01.01`, `00.01.01.01` - go as deep as you need
- **Permanent addresses** - once assigned, an address never changes and is never reused
- **Machine-readable manifest** - `jdx.manifest.yaml` maps every address in one file
- **Immutable corpus schema** - `jdx.config.yaml` locks the naming convention at init time
- **Agent-ready** - `agent_hint` fields on manifest nodes prime AI routing at schema-build time
- **Validator** - `jdx validate` checks your filesystem against the convention (CI-friendly)

---

## Install

```bash
python3 -m venv .venv
.venv/bin/pip install jdx
# or from source:
# .venv/bin/pip install -e .
```

---

## Quick Start

```bash
# Initialize a corpus
jdx init hexaxia-technologies --org HXT --context-type client

# Add nodes (parent-first)
jdx add 00 Admin "Company governance - legal, compliance, registrations"
jdx add 00.01 Business-Registration "Incorporation certificates and filings"
jdx add 02 Clients "One subfolder per active client engagement"
jdx add 02.01 ULS "United Life Services - Indianapolis, IN"

# Validate your filesystem
jdx validate
```

For a full walkthrough, see [docs/quickstart.md](docs/quickstart.md).

---

## Commands

| Command | Description |
|---|---|
| `jdx init CORPUS` | Initialize a new corpus |
| `jdx add ADDRESS LABEL DESC` | Add a node to the manifest |
| `jdx ls [ADDRESS]` | List manifest nodes |
| `jdx find QUERY` | Search manifest by label or description |
| `jdx validate` | Validate corpus naming convention compliance |

See [docs/cli-reference.md](docs/cli-reference.md) for the complete reference.

---

## Naming Convention

**Folders:** `{address}-{Title-Cased-Label}/`

```
00-Admin/
00.01-Business-Registration/
00.01.01-State-Filings/
```

**Files:** `{address}-[{ORG}-][{CONTEXT}-]{descriptor}[-{YYMMDD}].ext`

```
00.01.01-HXT-articles-of-incorporation-260115.pdf
02.01.03-HXT-ULS-msa-amendment-260527.md
```

ORG and CONTEXT codes come from `jdx.config.yaml` and are set once at corpus init.

---

## Core Rules

1. Addresses are permanent. Never renumber. Never reuse a retired address.
2. `jdx.config.yaml` is immutable after init. Changing it is a breaking change.
3. Retire a node by setting `deprecated: true` in the manifest - never delete the entry.
4. 4 levels of depth covers most organizations. Earn deeper levels.

---

## Documentation

| Document | Description |
|---|---|
| [docs/quickstart.md](docs/quickstart.md) | Walkthrough: build a corpus from scratch |
| [docs/concepts.md](docs/concepts.md) | Core concepts: addresses, manifest, config |
| [docs/cli-reference.md](docs/cli-reference.md) | Complete CLI reference |
| [docs/spec.md](docs/spec.md) | Full JDX design specification |
| [CHANGELOG.md](CHANGELOG.md) | Release notes |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Development setup and contribution guidelines |

---

## Status

JDX is at **v0.1.0** - a working POC of the standard and CLI tool. The addressing system,
manifest schema, naming convention, and validator are stable. The following are designed but
deferred to later versions:

- Agent navigation spec
- Document Passport integration
- Federation (multi-corpus addressing)

---

## License

Apache 2.0 - see [LICENSE](LICENSE) for details.
