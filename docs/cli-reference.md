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

## das init

Initialize a new DAS corpus in the specified directory.

**Usage:**

```
das init CORPUS [OPTIONS]
```

**Arguments:**

| Argument | Required | Description |
|---|---|---|
| `CORPUS` | Yes | Corpus slug, lowercase hyphenated (e.g. `hexaxia-technologies`) |

**Options:**

| Option | Default | Description |
|---|---|---|
| `--org TEXT` | None | Org code prepended to filenames (e.g. `HXT`). 2-5 uppercase letters. |
| `--context-type TEXT` | None | Secondary identifier type: `client`, `project`, `dept`, or `none` |
| `--date-format TEXT` | `YYMMDD` | Date format for filenames. `YYMMDD` is the defined format. Omit or pass empty string to exclude dates. |
| `--path PATH` | `.` | Directory to initialize the corpus in |

**Exit codes:**

| Code | Condition |
|---|---|
| 0 | Corpus initialized successfully |
| 1 | `das.config.yaml` already exists (corpus already initialized) |

**What it creates:**

- `das.config.yaml` - corpus configuration (immutable after this point)
- `das.manifest.yaml` - empty corpus manifest

**Examples:**

```bash
# Minimal corpus (no org code, no context type)
das init my-corpus

# Full config with org and client context
das init hexaxia-technologies --org HXT --context-type client

# Initialize in a specific directory
das init my-corpus --path /home/user/Documents/corpus

# Exclude dates from filenames
das init my-corpus --org HXT --date-format ""
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
| 1 | Corpus not initialized, address already exists, or parent address missing |

**Notes:**

- Nodes must be added parent-first. `00.01` cannot be added before `00` exists.
- Address format is validated: two-digit segments separated by dots (`00`, `00.01`, `00.01.01`).
- The node type (`area`, `category`, `subcategory`, `context`) is inferred from address depth.
- Once added, an address is permanent and cannot be reassigned.

**Examples:**

```bash
# Add a top-level area
das add 00 Admin "Company governance - legal, compliance, registrations"

# Add a category
das add 00.01 Business-Registration "Incorporation certificates and filings"

# Add a subcategory with an agent hint
das add 02.01 ULS "United Life Services - Indianapolis, IN" \
  --agent-hint "Primary MSP client. Contracts in 02.01.01, projects in 02.01.03."

# Add in a non-current-directory corpus
das add 04 Marketing "Brand, campaigns, content" --path /mnt/d/docs/corpus
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
| Address format | Address segments must be exactly two digits (`00`-`99`) |
| Folder casing | Folder label must start with an uppercase letter (`00-Admin`, not `00-admin`) |
| Manifest registration | Every folder's address must be registered in `das.manifest.yaml` |
| File-to-folder match | A file's address must match its parent folder's address |

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
```
