# Passport Placement: Embedded vs Sidecar

Where does a passport live? For Markdown the answer is settled: a YAML block inside a leading
HTML comment, embedded in the file itself ([passports.md](passports.md)). But real corpora are
dominated by formats that are not Markdown - PDF, DOCX, spreadsheets, images, datasets,
archives - and a "document standard" that only describes `.md` files has a hole where most
documents live. This document covers the design space (embedding metadata inside a file versus
carrying it in a companion sidecar), surveys what each major format can natively hold, and
states the standard's posture: **embedded for plain-text formats, sidecar for everything
else, and the plain-text representation is always the source of truth.**

---

## The two placements

**Embedded** - the passport travels inside the document file itself.

| Pro | Con |
|---|---|
| Cannot be orphaned: metadata moves with the file, always | Requires a format-specific writer and reader per file type |
| One artifact to manage, copy, and share | Modifies the original file - breaks checksums, signatures, and verbatim provenance |
| Survives any reorganization that moves whole files | Invisible to `grep`, `cat`, and a RAG indexer unless format-specific extraction runs first |
| | Some formats have no safe place to put it at all |

**Sidecar** - the passport is a companion `.md` file at the same address, next to the artifact.

| Pro | Con |
|---|---|
| Format-agnostic: works for any file type, including ones that do not exist yet | Two files that must stay together - a move that takes one and not the other orphans the metadata |
| Plain text: greppable, diffable, RAG-indexable with zero extraction tooling | Requires a pairing convention so tools and humans know which sidecar describes which artifact |
| The artifact is filed verbatim and never modified - checksums, signatures, and provenance stay intact | Slightly more visual noise in a folder listing |
| The summary (the RAG routing signal) is readable by the same pipeline that reads every other passport | |

The tension is real: embedding optimizes for *inseparability*, sidecars optimize for
*legibility*. DAS weighs legibility heavier, because the passport's highest-leverage field is
the `summary`, and a summary that retrieval and humans cannot read without format-specific
extraction machinery is not doing its job. The deterministic-floor thesis applies to metadata
too: a passport you can `cat` is part of the floor; a passport locked inside a binary
container is not.

---

## What formats can natively hold

A survey of the embedding options per format family, and why each falls short as the primary
home for a passport:

| Format family | Native metadata affordance | Why it is not the primary home |
|---|---|---|
| Markdown, plain text, source code | Comment block (HTML comment, `#` header) | It IS the primary home - plain text, greppable, no extraction needed |
| PDF | XMP packet / document info dictionary | Machine-readable but invisible to grep and RAG without a PDF-aware extractor; editing it alters the file (signature/checksum churn) |
| DOCX / XLSX / PPTX (OOXML) | `docProps/custom.xml` custom properties | Buried inside a ZIP container; same extraction and file-mutation problems as PDF |
| Images (PNG, JPEG, TIFF) | EXIF / XMP / IPTC | Field-size limits, inconsistent tool support, stripped silently by many pipelines |
| Data files (CSV, JSON, logs, captures) | None safe (a header row or comment corrupts the data for consumers) | No in-band location exists at all |
| Archives, binaries, proprietary formats | None | No in-band location exists at all |

The pattern is consistent: outside plain text, native metadata is either invisible to the
plain-text toolchain, mutates the artifact, or does not exist. No single embedding mechanism
covers the formats a real corpus contains.

---

## The standard's posture

1. **Plain-text formats embed.** Markdown (and by extension plain text and source files)
   carries the passport in a leading comment block, exactly as [passports.md](passports.md)
   defines. Embedded placement is correct here because the file is already part of the
   plain-text floor.

2. **Everything else gets a sidecar.** A non-text artifact is filed verbatim - never modified -
   and a companion `.md` passport at the same address describes it. This is already the
   practice in the data/research layout pattern
   ([corpus-layout-patterns.md](corpus-layout-patterns.md#pattern-3-data--research-corpus)),
   generalized here to any non-text document: a PDF contract, a spreadsheet, a slide deck, an
   image. Pattern 3's provenance fields (`source`, `license`, and friends) extend naturally to
   any sidecar.

3. **The plain-text representation is always the source of truth.** If a PDF also carries XMP
   metadata, or a DOCX has custom properties, those are at best mirrors. The sidecar is what
   the validator will check, the RAG layer indexes, and a human reads. Mirroring into native
   metadata is permitted and unmanaged - the standard neither requires nor reads it.

4. **Pairing convention.** The sidecar shares the artifact's address and lives in the same
   addressed folder. The recommended shape, following Pattern 3, is one addressed subfolder
   per artifact, holding the artifact and its passport:

   ```
   02.01.01-Contracts/
     02.01.01-contract-msa.pdf          <- the artifact, verbatim
     02.01.01-contract-msa.md           <- its sidecar passport
   ```

   The shared address prefix is the join key. A reader - human or agent - that finds either
   file can locate the other with one `ls`.

5. **Integrity fields for binaries.** A sidecar describing an artifact it does not contain
   should record enough to detect drift. Recommended optional fields, extending the Pattern 3
   provenance set:

   ```yaml
   artifact: "02.01.01-contract-msa.pdf"   # the file this passport describes
   checksum: "sha256:..."                  # detects silent modification or replacement
   ```

---

## Known limitations and open research

Stated plainly, in the spirit of the position paper's Section 7:

- **Orphaning is real and currently unchecked.** Nothing in the tool today verifies that every
  non-text artifact has a sidecar, or that a sidecar's `artifact` field points at a file that
  exists. Reverse validation (artifact-sidecar pairing as a `das validate` check) is the
  natural tooling extension and is deferred.
- **Extraction-based ingestion is an open pipeline question.** For a corpus migrating thousands
  of PDFs, generating sidecar summaries is exactly the kind of work an ingestion/ETL pass
  should automate (see the ingestion path in
  [dynamic-corpus-management.md](dynamic-corpus-management.md)). Until such tooling exists,
  sidecar authoring for legacy documents is manual - the same honest cost the migration FAQ
  concedes.
- **Mirroring policy is unstudied.** Whether writing the passport summary into PDF XMP or OOXML
  custom properties ever pays for itself (search integration in DMS tools, for example) has not
  been measured. The standard's position is only that mirrors must never become the source of
  truth.
- **The benchmark evidence does not yet cover sidecars.** The measured RAG-routing results were
  produced on embedded Markdown passports. Sidecar summaries should behave identically to the
  indexer (they are the same plain text), but that equivalence is assumed, not measured.

The direction of the standard is unchanged by any of these: keep the metadata in plain text,
keep the artifact verbatim, and let the address pair them.
