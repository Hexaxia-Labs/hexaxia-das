# JDX: Johnny Decimal Extended

A corpus organization standard and CLI tool for large document collections.
Every folder and file gets a permanent numeric address. Every corpus gets a
machine-readable manifest. Agents and humans navigate the same address space.

See [docs/spec.md](docs/spec.md) for the full design specification.

## Install

    python3 -m venv .venv
    .venv/bin/pip install -e .

## Commands

### Initialize a corpus

    jdx init my-corpus --org HXT --context-type client

Creates `jdx.config.yaml` and `jdx.manifest.yaml` in the current directory.

### Add a node

    jdx add 00 Admin "Company governance - legal, compliance, registrations"
    jdx add 00.01 Business-Registration "Incorporation certificates and filings"
    jdx add 00.01.01 State-Filings "Indiana and Delaware state-level documents"

Nodes must be added parent-first. Addresses are permanent once added.

### List nodes

    jdx ls              # all nodes
    jdx ls 00           # node 00 and its direct children

### Search

    jdx find client     # search labels and descriptions
    jdx find invoice

### Validate

    jdx validate

Checks that all folders and files in the corpus follow the JDX naming
convention and that all folder addresses are registered in the manifest.
Exits 0 if clean, 1 if errors found.

## Naming Convention

**Folders:** `{address}-{Title-Cased-Label}/`

    00-Admin/
    00.01-Business-Registration/
    00.01.01-State-Filings/

**Files:** `{address}-[{ORG}-][{CONTEXT}-]{descriptor}[-{YYMMDD}].ext`

    00.01.01-HXT-articles-of-incorporation-260527.md
    02.01.03-HXT-ULS-msa-amendment.md

## Rules

1. Addresses are permanent. Never renumber. Never reuse a retired address.
2. `jdx.config.yaml` is immutable after init. Changing it is a breaking change.
3. Retire a node by setting `deprecated: true` in the manifest - never delete it.
4. 4 levels of depth covers most organizations. Earn deeper levels.
