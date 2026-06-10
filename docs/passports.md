# Document Passports

A Document Passport is a per-document metadata container embedded inside the file it describes. It records the document's DAS address, type, status, title, tags, dates, and a short summary. Because the DAS address is the passport's primary key, documents become queryable by address without filesystem traversal, and the `summary` field is the signal a RAG system uses to route a query to the right document. This guide is a teaching reference; the normative definition is spec section 10.2 in [spec.md](spec.md#102-document-passports), and this document does not contradict it.

## Where It Lives and Its Format

In a Markdown file the passport is a YAML block inside a leading HTML comment, placed before the first heading. Keeping it in an HTML comment means it travels with the document and renders invisibly, while remaining easy to parse. For non-Markdown documents (PDF, DOCX, data files, binaries) the passport is a companion sidecar instead - see [passport-formats.md](passport-formats.md) for the embedded-vs-sidecar design space and the standard's posture.

```markdown
<!--
passport:
  title: "NetBird ZTNA Deployment Runbook"
  type: runbook
  status: active
  tags: [ACME, NETBIRD]
  das_address: "02.01.04"
  created: "2026-05-09"
  modified: "2026-05-28"
  summary: "Six-phase runbook to deploy NetBird ZTNA for Acme Corp (ACME).
            Current blockers: firewall ports 51820/UDP pending ACME IT approval; MFA
            enrollment for 3 admins; UAT sign-off deferred to May 30."
-->

# NetBird ZTNA Deployment Runbook
```

## Field Reference

| Field | Required | Meaning / rules |
|---|---|---|
| `das_address` | Yes | The document's DAS address. Primary key / location identifier (section 10.2). Must match the file's address. |
| `type` | Yes | Authoritative document type. Controlled vocabulary - the same 17 type slugs as filenames (section 5.4). The filename type slug is a navigation echo; this field is authoritative for indexing. |
| `status` | Yes | Lifecycle state: `draft`, `active`, `deprecated`, or `archived`. |
| `title` | Yes | Human-readable title, specific enough to surface in search. |
| `summary` | Yes (field present) | 2-5 sentences. The entire RAG routing signal. Content rules in `writing-passport-summaries.md`. May be empty in a `draft` but an `active` document must fill it (see lifecycle). |
| `tags` | No | List of tag codes from the corpus `tags` vocabulary (`das.config.yaml`, section 4). A passport MAY carry multiple tags even though a filename carries at most one (section 5.3 rules 6-7). |
| `created` | No | Creation date, `YYYY-MM-DD`. |
| `see_also` | No | List of related document addresses, plain (`02.01.03`) or federated (`ORG:02.01.03`). See `federation.md`. |
| `modified` | No | Last-modified date, `YYYY-MM-DD`. |

A few notes on usage:

- `das_address` must match the address of the file the passport is embedded in. It is the join key between the document and the rest of the corpus, so a mismatch breaks address-based lookup.
- `type` is the authoritative document type and must be drawn from the controlled vocabulary in section 5.4 (runbook, plan, spec, design, strategy, playbook, proposal, contract, report, catalog, lead, post, template, reference, procedure, email, log). The filename's type slug is only a navigation echo; this field is what indexing trusts.
- `status` records where the document sits in its lifecycle. See the next section for the four states and their rules.
- `title` should be specific enough to be recognizable in search results, not a generic label.
- `summary` is the highest-leverage field and the only one that drives RAG routing. For how to write a good summary - what to include, what to avoid, and worked examples - see [writing-passport-summaries.md](writing-passport-summaries.md). This guide does not repeat that craft.
- `tags` may list more than one code, each a valid tag code (2-5 characters, starting with an uppercase letter, then uppercase letters and/or digits - e.g. `ACME`, `NW7`, `M365`), all drawn from the corpus `tags` vocabulary in `das.config.yaml` (section 4). A filename carries at most one tag; the passport is where additional tag dimensions live (section 5.3 rules 6-7).
- `created` and `modified` are optional dates in `YYYY-MM-DD` form.

## Lifecycle

The `status` field moves through four states:

- `draft` - newly created, for example by `das new`. A draft MAY have an empty `summary`.
- `active` - in use. An active document MUST have a written `summary`, since this is what makes it findable.
- `deprecated` - superseded but retained. Dropped from primary navigation but not deleted.
- `archived` - retired.

The key rule is the draft-to-active transition: an empty `summary` is acceptable while a document is a `draft`, but promoting it to `active` requires filling the `summary` in.

## Relationships

A passport does not stand alone. It connects to three other parts of the system.

**Filename versus passport.** The filename carries navigation signals: the address, an optional single tag, and the type slug. The passport carries authoritative metadata: the full type, multiple tags, dates, and the summary. The filename is what a human or agent reads while walking the tree; the passport is what indexing and retrieval read. Where they overlap (type, the optional filename tag), the passport is authoritative.

**Manifest versus passport.** The manifest (`das.manifest.yaml`) indexes addresses and folders at the corpus level. The passport is per-document metadata embedded in the file. The two are joined by `das_address`. Passports are not stored in the manifest; each lives in its own document.

**RAG.** The `summary` is embedded and is the rag-nav signal that routes a query to a document. The quality of that summary determines routing accuracy. For how to write them well see [writing-passport-summaries.md](writing-passport-summaries.md).

## Creating a Passport with das new

For `.md` files, `das new` scaffolds a passport stub: it sets `status: draft` and leaves the `summary` empty, filling in the structural fields it can derive (such as `das_address`, `type`, `title`, and dates). The author then writes the `summary` and promotes `status` to `active`. See the `das new` entry in [cli-reference.md](cli-reference.md) for the exact fields scaffolded and the command's options.

## Non-Markdown Files

Embedded passports are Markdown-only today. The HTML-comment block described above applies to `.md` files. Passport storage for non-Markdown documents is deferred and will be designed separately; this matches the warning `das new` emits for non-`.md` files.
