# Hexaxia DAS CLI Reference

Complete reference for the `das` command-line tool.

---

## Per-Command Options

Every command accepts a `--path` option to specify a corpus root directory other than the current directory. Pass it to the specific subcommand, not to `das` itself.

```bash
das --help
das <command> --help
```

---

## das --version

Print the installed `das` package version and exit.

**Usage:**

```
das --version
```

Reports the package version (from `das.__version__`). Does not require an initialized corpus.

---

## das init

Initialize a new DAS corpus in the specified directory.

**Usage:**

```
das init CORPUS [OPTIONS]
```

**Arguments:**

| Argument | Required | Description |
|---|---|---|
| `CORPUS` | Yes | Corpus slug, lowercase hyphenated (e.g. `atlas-technologies`) |

**Options:**

| Option | Default | Description |
|---|---|---|
| `--org TEXT` | None | The corpus's namespace identifier (e.g. `ATL`), recorded in `das.config.yaml` and used as the federation prefix (`ATL:address`). Not added to filenames. |
| `--tag CODE=description` | None | Tag vocabulary entry. Repeatable. Code is 2-5 characters: it starts with an uppercase letter, then uppercase letters and/or digits (e.g. `ACME`, `NW7`, `M365`). Omit entirely for corpora that do not use filename tags - no `tags` block is written. |
| `--naming-style STYLE` | `das-address` | The corpus's declared filename convention written into the `naming` block: `das-address` (the default address-first rules), `slug-date` (legacy slug-first files with no address prefix), or `custom`. Each style is seeded with sensible `pattern_draft` / `pattern_published` templates. An invalid style exits 1. See `docs/corpus-conventions.md`. |
| `--path PATH` | `.` | Directory to initialize the corpus in |

**Exit codes:**

| Code | Condition |
|---|---|
| 0 | Corpus initialized successfully |
| 1 | `das.config.yaml` already exists, malformed `--tag` (no `=`), or invalid tag code/description |

**What it creates:**

- `das.config.yaml` - corpus configuration (immutable after this point)
- `das.manifest.yaml` - empty corpus manifest

**Examples:**

```bash
# Minimal corpus (no org code)
das init my-corpus

# Full config with org code
das init atlas-technologies --org ATL

# Define a filename tag vocabulary (repeat --tag per entry)
das init atlas-technologies --tag ACME="Acme Corp client" --tag GBX="Globex client"

# Declare a non-default naming convention (e.g. legacy slug-first marketing files)
das init labs --naming-style slug-date

# Initialize in a specific directory
das init my-corpus --path /home/user/Documents/corpus
```

---

## das add

Add a node to the corpus manifest.

**Usage:**

```
das add ADDRESS LABEL DESCRIPTION [OPTIONS]
```

**Arguments:**

| Argument | Required | Description |
|---|---|---|
| `ADDRESS` | Yes | DAS address (e.g. `00`, `00.01`, `00.01.01`) |
| `LABEL` | Yes | Human-readable folder label, Title-Cased and hyphenated (e.g. `Business-Registration`) |
| `DESCRIPTION` | Yes | One-sentence description of what belongs here |

**Options:**

| Option | Default | Description |
|---|---|---|
| `--agent-hint TEXT` | None | Optional routing guidance for AI agents |
| `--path PATH` | `.` | Corpus root directory |

**Exit codes:**

| Code | Condition |
|---|---|
| 0 | Node added successfully |
| 1 | Corpus not initialized, invalid address format, address already exists, or parent address missing |

**Notes:**

- Nodes must be added parent-first. `00.01` cannot be added before `00` exists.
- Address format is validated: numeric segments of two or more digits separated by dots (`00`, `00.01`, `00.01.01`).
- The node type (`area`, `category`, `subcategory`, `context`) is inferred from address depth.
- Once added, an address is permanent and cannot be reassigned.

**Examples:**

```bash
# Add a top-level area
das add 00 Admin "Company governance - legal, compliance, registrations"

# Add a category
das add 00.01 Business-Registration "Incorporation certificates and filings"

# Add a subcategory with an agent hint
das add 02.01 ACME "Acme Corp - Springfield, IL" \
  --agent-hint "Primary MSP client. Contracts in 02.01.01, projects in 02.01.03."

# Add in a non-current-directory corpus
das add 04 Marketing "Brand, campaigns, content" --path /mnt/d/docs/corpus
```

---

## das new

Create a new spec-v0.3-conformant document file at an address.

**Usage:**

```
das new ADDRESS TYPE DESCRIPTOR [OPTIONS]
```

**Arguments:**

| Argument | Required | Description |
|---|---|---|
| `ADDRESS` | Yes | DAS address (e.g. `00`, `02.01.04`). Must resolve to exactly one folder on disk. |
| `TYPE` | Yes | Type slug from the spec 5.4 vocabulary (e.g. `reference`, `runbook`, `contract`) |
| `DESCRIPTOR` | Yes | Lowercase-hyphenated descriptor (e.g. `netbird-ztna`, `company-profile`) |

**Options:**

| Option | Default | Description |
|---|---|---|
| `--tag CODE` | None | Tag code, inserted into the filename after the address. Must be a key in the config `tags` vocabulary. |
| `--ext TEXT` | `md` | File extension. Only `.md` files receive a passport stub; other extensions are created bare with a stderr note. |
| `--published` | off | Generate the filename from the corpus `pattern_published` template instead of `pattern_draft`. Adds the publish date. Exits 1 if the corpus declares no `pattern_published`. |
| `--date YYMMDD` | today | Publish date for `--published` files (six digits). Defaults to today when omitted. A non-`YYMMDD` value exits 1. Ignored for drafts. |
| `--path PATH` | `.` | Corpus root directory |

**What it does:**

- Validates the address format, the type slug, the descriptor, and (when given) the tag against the config vocabulary.
- Resolves the address to its folder by scanning for `{address}-*` directories whose address segment equals the given address.
- Builds the filename from the corpus's declared naming convention (the `naming` block in `das.config.yaml`, defaulting to the standard `{address}-[{TAG}-]{type}-{descriptor}.{ext}` pattern). `--published` selects `pattern_published`, which adds a `{YYMMDD}` publish date; the default draft pattern omits the date (a draft date churns on reschedule). Writes the file into the resolved folder.
- For `.md` files, scaffolds a passport stub (an HTML-comment block with `title`, `type`, `status: draft`, optional `tags`, `das_address`, `created`, and an empty `summary`) followed by a `# Title` heading. The empty `summary` is the entire RAG signal and must be filled in.

See [passports.md](passports.md) for the full passport field reference and lifecycle.
- Does not touch the manifest and does not create folders.

**Exit codes:**

| Code | Condition |
|---|---|
| 0 | File created (including non-`.md` files, which also print a stderr note) |
| 1 | Corpus not initialized; invalid address, type, descriptor, or tag; no folder or multiple folders found for the address; or a file with that name already exists |

**Examples:**

```bash
# Create a reference markdown file with a passport stub
das new 00 reference company-profile

# Create a tagged runbook (tag must be in the config vocabulary)
das new 02.01.04 runbook netbird-ztna --tag ACME

# Create a non-markdown file (bare, no passport stub)
das new 00 report audit --ext pdf

# Create a published file (adds the publish date from pattern_published)
das new 01.01.01 post you-have-a-corpus --published --date 260603

# Create in a specific corpus
das new 04 post q2-social --path /mnt/d/docs/corpus
```

---

## das ls

List nodes in the corpus manifest.

**Usage:**

```
das ls [ADDRESS] [OPTIONS]
```

**Arguments:**

| Argument | Required | Description |
|---|---|---|
| `ADDRESS` | No | If provided, show this node and its direct children only |

**Options:**

| Option | Default | Description |
|---|---|---|
| `--path PATH` | `.` | Corpus root directory |

**Exit codes:**

| Code | Condition |
|---|---|
| 0 | Always (even if no results) |
| 1 | Corpus not initialized |

**Output format:**

```
  {address:<20} {label:<30} {description}[deprecated]
```

Deprecated nodes are shown with a `[deprecated]` suffix.

**Examples:**

```bash
# List all nodes
das ls

# List node 02 and its direct children
das ls 02

# List in a specific corpus
das ls --path /mnt/d/docs/corpus
```

---

## das find

Search the manifest by label or description.

**Usage:**

```
das find QUERY [OPTIONS]
```

**Arguments:**

| Argument | Required | Description |
|---|---|---|
| `QUERY` | Yes | Search term (case-insensitive, substring match) |

**Options:**

| Option | Default | Description |
|---|---|---|
| `--path PATH` | `.` | Corpus root directory |

**Exit codes:**

| Code | Condition |
|---|---|
| 0 | Always (even if no results) |
| 1 | Corpus not initialized |

**Notes:**

- Search is case-insensitive and matches substrings in both the label and description fields.
- Deprecated nodes are included in results.

**Examples:**

```bash
# Find anything related to "client"
das find client

# Find anything with "invoice" in the label or description
das find invoice

# Search in a specific corpus
das find compliance --path /mnt/d/docs/corpus
```

---

## das validate

Validate corpus naming convention compliance.

**Usage:**

```
das validate [OPTIONS]
```

**Options:**

| Option | Default | Description |
|---|---|---|
| `--strict` | off | Enforces the full v0.3 filename format, including a valid `{type}` slug from the spec 5.4 vocabulary; a missing or unknown type is an error. Strict mode also requires every addressed file to carry a present, lowercase-hyphenated `{descriptor}` (spec 5.2 / 5.3) and requires every word of a folder label to be Title-Cased, starting with an uppercase letter or digit (spec 5.1). Default validation does not perform these checks. |
| `--path PATH` | `.` | Corpus root directory |

**Exit codes:**

| Code | Condition |
|---|---|
| 0 | Corpus is valid - no errors found |
| 1 | One or more validation errors found, or corpus not initialized |

**What is checked:**

| Check | Rule |
|---|---|
| Address prefix | Every folder and file name must start with a valid DAS address |
| Address format | Address segments are two or more digits; two-digit (`00`-`99`) is the default |
| Folder casing | Folder label must start with an uppercase letter (`00-Admin`, not `00-admin`) |
| Manifest registration | Every folder's address must be registered in `das.manifest.yaml` |
| File-to-folder match | A file's address must match its parent folder's address |
| Root file registration | Address-bearing files at the corpus root are cross-checked against the manifest |
| Declared naming convention | When the config `naming` block declares a non-address `style` (`slug-date` or `custom`), file names are checked against the declared `pattern_draft` / `pattern_published` templates (compiled to a regex) instead of the address-first rules; a file matching neither is an error. Folders stay address-based. The default `das-address` style (and any corpus with no `naming` block) applies the address rules below unchanged. See `docs/corpus-conventions.md`. |
| Filename tag vocabulary | When the config defines a `tags` vocabulary, a filename's tag (the 2-5 character token immediately after the address - starting with an uppercase letter, then uppercase letters and/or digits) must be a key in that vocabulary; an unknown tag is an error. Enforcement is skipped entirely when no `tags` vocabulary is defined. |
| Filename type slug (`--strict` only) | With `--strict`, every addressed file's `{type}` slug (the first post-address token, or the second when a tag is present) must be one of the spec 5.4 type slugs; a missing or unknown type is an error. Folders are exempt. Default validation does not perform this check. |
| Filename descriptor (`--strict` only) | With `--strict`, every addressed file must carry a present, lowercase-hyphenated `{descriptor}` after the `{type}` token (spec 5.2 / 5.3); a missing descriptor, or one with uppercase letters or non-hyphen separators, is an error. Folders are exempt. Default validation does not perform this check. |
| Folder label casing (`--strict` only) | With `--strict`, every word of a folder label (the hyphen-separated tokens after the address) must be Title-Cased, starting with an uppercase letter or digit (spec 5.1); a lowercase-led word is an error. Default validation does not perform this check. |

**Skipped items:**

The validator skips: `das.config.yaml`, `das.manifest.yaml`, `das.migration.md`, `README.md`,
hidden files and directories (starting with `.`), and any items inside hidden directories.

**Example output (valid corpus):**

```
Corpus is valid.
```

**Example output (invalid corpus):**

```
3 validation error(s):
  02-clients: Folder label must be Title-Cased and hyphenated (e.g. '00-Admin')
  02-Clients/02.01-Northstar-Logistics/invoice.pdf: No DAS address prefix found
  02-Clients/02.01-Northstar-Logistics/02.01.01-Contracts/02.01-ATL-NSL-msa.pdf: File address '02.01' does not match parent folder address '02.01.01'
```

**Examples:**

```bash
# Validate current directory corpus
das validate

# Validate a specific corpus
das validate --path /mnt/d/docs/corpus

# Use in CI - non-zero exit if invalid
das validate || echo "Corpus has naming violations"

# Strict mode also enforces the {type} slug against the spec 5.4 vocabulary
das validate --strict
```
