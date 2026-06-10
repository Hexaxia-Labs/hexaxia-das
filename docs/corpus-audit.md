# Corpus Audit Guide

A corpus audit is a systematic review of a DAS corpus to verify that the filesystem,
manifest, and conventions are all consistent with each other. This guide describes when
to run an audit, what to check, and how to interpret and fix the results.

For ongoing health monitoring see the health signals table in `docs/dynamic-corpus-management.md`.
An audit is a deeper, point-in-time review rather than a continuous signal.

---

## When to run an audit

Run a corpus audit:
- Before publishing a corpus or adding it to the project registry
- Before handing a corpus off to a new maintainer or agent
- When `das validate` output is unexpectedly noisy (many errors appearing at once)
- When the corpus has been batch-filed by an automated tool (ETL ingestion, bulk import)
- Periodically for active corpora (quarterly is a reasonable cadence for large corpora)
- When a corpus has been idle for more than a few months - passports go stale, conventions drift

---

## Audit layers

A full audit covers four layers:

1. **Filesystem / naming** - Are all files and folders named correctly?
2. **Manifest completeness** - Does every file have a manifest entry, and every manifest
   entry have a file?
3. **Passport quality** - Are passport fields filled in correctly and completely?
4. **Convention compliance** - Does the corpus follow its own declared conventions?

These can be run in any order. The naming audit (`das validate`) is always the starting
point because it will surface the most errors the fastest.

---

## Layer 1: Filesystem / naming audit

Run the validator:

```bash
das validate
```

For a strict audit that also checks type slugs and folder labels:

```bash
das validate --strict
```

**Interpreting the output:**

| Error message | Cause | Fix |
|---------------|-------|-----|
| `No DAS address prefix found` | File missing the `{address}-` prefix | Rename the file to include the address |
| `File address X does not match parent folder address Y` | File is in the wrong folder | Move to the folder whose address matches the file's address |
| `Unknown tag 'ABC'` | Tag not in config vocabulary | Either add the tag to config or remove it from the filename |
| `Folder label not Title-Cased` | Folder name formatting error | Rename the folder; every word title-cased, hyphen-separated |
| `Address X not in manifest` | File exists but has no manifest entry | `das add X label description` |
| `Manifest address X has no file` | Manifest entry exists but no file at that address | Either create the file or deprecate the manifest node |

**Common batch-filing issues:**

After automated ingestion, the most common errors are missing manifest entries (files filed
without `das add`) and address/folder mismatches (files placed at the wrong depth). Fix
manifest entries first, then rerun to check for remaining issues.

---

## Layer 2: Manifest completeness audit

The validator catches `address not in manifest` for existing files, but it does not catch
the reverse direction: manifest nodes with no corresponding file (unless you use `--strict`).

Run the reverse check manually:

```bash
# Extract all addresses from the manifest
python3 -c "
import yaml
m = yaml.safe_load(open('das.manifest.yaml'))
for addr, node in m.get('nodes', {}).items():
    if not node.get('deprecated'):
        print(addr)
" | sort > /tmp/manifest-addresses.txt

# Find all addressed files and folders in the corpus
find . -mindepth 1 -not -path './.git/*' | \
  grep -oP '^\./[0-9][0-9](\.[0-9][0-9])*' | \
  sort -u > /tmp/filesystem-addresses.txt

# Addresses in manifest but not on filesystem
comm -23 /tmp/manifest-addresses.txt /tmp/filesystem-addresses.txt
```

Addresses in the manifest with no corresponding filesystem entry are usually:
- Nodes added speculatively before content arrived - deprecate if still empty after a
  reasonable time, or leave as placeholders if content is incoming
- Nodes whose content was moved but the old address was not deprecated - deprecate and
  update `das.migration.md`

---

## Layer 3: Passport quality audit

For corpora that use sidecar passports, a passport audit checks whether passports exist,
are filled in, and have no stale or contradictory fields.

**Check 1: Missing passports**

Every data/research artifact should have a passport. Find artifacts without one:

```bash
# Find .nc, .pdf, .csv files without a companion .md passport at the same address
find . -name '*.nc' -o -name '*.pdf' | while read f; do
    addr=$(basename "$f" | grep -oP '^[0-9]+(\.[0-9]+)*')
    dir=$(dirname "$f")
    if ! ls "$dir"/${addr}-*passport*.md "$dir"/${addr}-*note*.md 2>/dev/null | grep -q .; then
        echo "MISSING PASSPORT: $f"
    fi
done
```

**Check 2: Empty required fields**

For data/research corpora, `source` and `clearance` are mandatory:

```bash
find . -name '*-passport*.md' -o -name '*-note-*passport*' | xargs grep -l 'source: ""'
find . -name '*-passport*.md' -o -name '*-note-*passport*' | xargs grep -l 'clearance: ""'
```

Files with empty `source` must either have provenance filled in or be marked
`clearance: internal` as a minimum. No unsourced files should be `clearance: public`.

**Check 3: Stale valid_until fields**

For agent memory corpora, entries with a `valid_until` date in the past are stale:

```bash
TODAY=$(date +%Y-%m-%d)
find . -name '*.md' -exec grep -l 'valid_until:' {} \; | while read f; do
    val_until=$(grep 'valid_until:' "$f" | grep -oP '\d{4}-\d{2}-\d{2}')
    if [[ -n "$val_until" && "$val_until" < "$TODAY" ]]; then
        echo "STALE: $f (expired $val_until)"
    fi
done
```

Stale entries should be deprecated (not deleted) and updated or superseded.

**Check 4: verified_good without verification_method**

A passport can claim `verified_good: true` without documenting how - this is a silent
trust gap:

```bash
grep -rl 'verified_good: true' . | xargs grep -L 'verification_method:'
```

For each match, either add `verification_method` or roll back `verified_good` to `false`
until proper verification is documented.

---

## Layer 4: Convention compliance audit

Check the corpus against its own declared conventions (the `00.01-Conventions` document).

**Convention areas to check:**

1. **Naming style consistency.** If the corpus declared `slug-date` naming, are all files
   following the slug-date pattern? Run `das validate` - if the naming block is correct in
   config, the validator will enforce it.

2. **Tag usage.** Are tags being used consistently? A corpus that declared `MK1` and `MK2`
   as device tags should have those tags on every device-specific file. A file with no tag
   in a multi-device corpus is an inconsistency worth reviewing.

3. **Address depth.** Is the depth consistent with the declared conventions? Files at depth 4
   in a corpus that declared max depth 3 are either legitimate exceptions or convention drift.

4. **Segment width.** If the corpus declared three-digit addressing at the program level, are
   all program addresses three digits? Any two-digit addresses at that level are either pre-convention
   or misfiled.

5. **Passport schema.** Do all passports include the required fields for this corpus's pattern?
   The corpus conventions document should list the required fields.

---

## Audit report

For a formal audit, capture the output in a short report. The format does not need to be
elaborate - a bullet list of findings per layer is enough:

```markdown
# Corpus audit: foundry - 260604

## Layer 1: Naming (das validate)
- 0 errors

## Layer 2: Manifest completeness
- 3 manifest nodes with no file: 10.02.11, 10.02.12, 10.02.13 (placeholder nodes for programs
  not yet filed; leave in place, content incoming)

## Layer 3: Passport quality
- 2 passports with empty source field: 20.02.01, 20.02.02 (synthetic readings - marked source
  as SYNTHETIC-ATL)
- 0 stale valid_until entries (not applicable - this corpus does not use temporal validity)

## Layer 4: Convention compliance
- All MK1 device readings correctly tagged MK1
- All MK2 device readings correctly tagged MK2
- 1 reading (10.01.01) uses an extended field set not present in the other device's readings;
  this is documented in the coverage index

## Summary
Minor issues resolved. Corpus ready for publication.
```

File the audit report in `00-Meta` at the corpus's own address (e.g. `00.04-Audit-Log`).
This creates a traceable history of audit dates and findings.

---

## After the audit: repair priority

When an audit produces a list of issues, fix them in this order:

1. **Naming errors** (Layer 1): Structural violations that will cause `das validate` to
   exit non-zero. Fix these first - they block automated tooling and agent navigation.

2. **Missing manifest entries** (Layer 2): Files with no manifest entry are invisible to
   the manifest-first navigation protocol. Fix these before any agent work on the corpus.

3. **Clearance / provenance gaps** (Layer 3): Empty `source` or `clearance` on non-internal
   content is a publication risk. Fix before any public access.

4. **Convention drift** (Layer 4): Important for long-term corpus health but does not block
   immediate use. Schedule for the next maintenance pass.

---

*See also: `docs/dynamic-corpus-management.md`, `docs/passports.md`,
`docs/das-migration-convention.md`*
