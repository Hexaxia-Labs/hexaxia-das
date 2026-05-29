# Quickstart: Building Your First Hexaxia DAS Corpus

This guide walks you through initializing a DAS corpus, building out an address tree,
naming files correctly, and validating your corpus.

We'll use a fictional company called **Atlas Technologies** as the example. Atlas has:
- Multiple clients
- Internal admin and finance docs
- A marketing team

**Time to complete:** About 10 minutes.

---

## Prerequisites

Install Hexaxia DAS:

```bash
python3 -m venv .venv
.venv/bin/pip install -e ~/Projects/hexaxia-das
# or once published to PyPI:
# .venv/bin/pip install hexaxia-das
```

Verify the install:

```bash
.venv/bin/das --help
```

---

## Step 1: Initialize the Corpus

Create a directory for your corpus and initialize it:

```bash
mkdir ~/Documents/atlas-corpus
cd ~/Documents/atlas-corpus
das init atlas-technologies --org ATL --context-type client --date-format YYMMDD
```

This creates two files:

```
atlas-corpus/
  das.config.yaml
  das.manifest.yaml
```

`das.config.yaml` defines the naming schema. It is permanent - do not edit it after
documents exist. Verify it looks right:

```yaml
version: '1.0'
corpus: atlas-technologies
initialized: 2026-05-27
address_separator: .
manifest: das.manifest.yaml
org: ATL
context_type: client
date_format: YYMMDD
```

The `version` here is the schema (file format) version `"1.0"`, distinct from the tool version
(`0.3.0`) and the design spec version (`v0.3`). The `org` / `context_type` / `date_format` fields
are what the current `das` CLI writes. The design spec (v0.3) has since replaced the date/context
filename scheme with an optional `tags` vocabulary and a required `type` slug (used in Step 5
below); the CLI does not yet emit a `tags` block, so apply tags by hand for now.

---

## Step 2: Build the Address Tree

Add nodes parent-first. A node cannot be added before its parent exists.

**Add the top-level areas:**

```bash
das add 00 Admin "Company governance - legal, compliance, registrations"
das add 01 Finance "Accounting, invoicing, taxes, banking"
das add 02 Clients "One subfolder per active client engagement"
das add 03 HR "Hiring, onboarding, policies, team"
das add 04 Marketing "Brand, campaigns, content, SEO"
```

**Add categories under Admin:**

```bash
das add 00.01 Business-Registration "Incorporation certificates, jurisdiction filings"
das add 00.02 Insurance "Business liability and professional indemnity policies"
das add 00.03 Compliance "Regulatory compliance documents and audits"
```

**Add categories under Clients:**

```bash
das add 02.01 Northstar-Logistics "Northstar Logistics - Chicago, IL"
das add 02.02 Pinnacle-Health "Pinnacle Health Systems - Indianapolis, IN"
```

**Add subcategories under 02.01:**

```bash
das add 02.01.01 Contracts "MSA, SOWs, amendments"
das add 02.01.02 Correspondence "Emails, meeting notes, call logs"
das add 02.01.03 Projects "Active project deliverables"
```

---

## Step 3: Inspect the Manifest

List all nodes to see your address tree:

```bash
das ls
```

Output:

```
  00                   Admin                          Company governance - legal, compliance, registrations
  00.01                Business-Registration          Incorporation certificates, jurisdiction filings
  00.02                Insurance                      Business liability and professional indemnity policies
  00.03                Compliance                     Regulatory compliance documents and audits
  01                   Finance                        Accounting, invoicing, taxes, banking
  02                   Clients                        One subfolder per active client engagement
  02.01                Northstar-Logistics            Northstar Logistics - Chicago, IL
  02.01.01             Contracts                      MSA, SOWs, amendments
  02.01.02             Correspondence                 Emails, meeting notes, call logs
  02.01.03             Projects                       Active project deliverables
  02.02                Pinnacle-Health                Pinnacle Health Systems - Indianapolis, IN
  03                   HR                             Hiring, onboarding, policies, team
  04                   Marketing                      Brand, campaigns, content, SEO
```

List just Clients and its direct children:

```bash
das ls 02
```

Search for anything related to contracts:

```bash
das find contract
```

---

## Step 4: Create the Folder Structure

Create folders using the Hexaxia DAS naming convention: `{address}-{Title-Cased-Label}/`

```bash
mkdir -p 00-Admin/00.01-Business-Registration
mkdir -p 00-Admin/00.02-Insurance
mkdir -p 00-Admin/00.03-Compliance
mkdir -p 01-Finance
mkdir -p 02-Clients/02.01-Northstar-Logistics/02.01.01-Contracts
mkdir -p 02-Clients/02.01-Northstar-Logistics/02.01.02-Correspondence
mkdir -p 02-Clients/02.01-Northstar-Logistics/02.01.03-Projects
mkdir -p 02-Clients/02.02-Pinnacle-Health
mkdir -p 03-HR
mkdir -p 04-Marketing
```

---

## Step 5: Name Your Files

Files follow this pattern (see [docs/spec.md](spec.md) section 5.2):

```
{address}-[{TAG}-]{type}-{descriptor}.ext
```

The `type` is a required slug from the controlled vocabulary in spec section 5.4
(`contract`, `report`, `spec`, `lead`, ...). The `TAG` is optional and comes from the
`tags` vocabulary in `das.config.yaml`. Dates and org prefixes do not belong in filenames -
created/modified dates live in the document passport.

```bash
# Articles of incorporation (internal doc - address is unambiguous, no tag)
touch 00-Admin/00.01-Business-Registration/00.01-contract-articles-of-incorporation.pdf

# MSA for Northstar Logistics (NSL tag scopes the file to the client)
touch 02-Clients/02.01-Northstar-Logistics/02.01.01-Contracts/02.01.01-NSL-contract-msa.pdf

# SOW for a Northstar security audit project
touch 02-Clients/02.01-Northstar-Logistics/02.01.01-Contracts/02.01.01-NSL-contract-sow-security-audit.pdf

# A project deliverable
touch 02-Clients/02.01-Northstar-Logistics/02.01.03-Projects/02.01.03-NSL-design-network-diagram.pdf
```

Naming breakdown for `02.01.01-NSL-contract-msa.pdf`:

| Component | Value | Source |
|---|---|---|
| Address | `02.01.01` | The containing folder's address |
| TAG | `NSL` | Optional code from the `tags` vocabulary (Northstar Logistics client) |
| type | `contract` | Required slug from the spec section 5.4 vocabulary |
| Descriptor | `msa` | What the document is |

The TAG is optional. Apply one when the file travels out of folder context, belongs to an
entity an agent may need to enumerate corpus-wide, or needs in-folder disambiguation - see
spec section 5.3 rule 6. Internal docs where the folder already gives unambiguous context
do not need a tag.

---

## Step 6: Validate the Corpus

Run the validator to check that all folders and files follow the naming convention:

```bash
das validate
```

If everything is clean:

```
Corpus is valid.
```

If there are issues, the validator tells you what is wrong and where:

```
2 validation error(s):
  02-Clients/02.01-northstar-logistics: Folder label must be Title-Cased and hyphenated (e.g. '00-Admin')
  02-Clients/02.01-Northstar-Logistics/invoice.pdf: No DAS address prefix found
```

Fix the issues and run `das validate` again until it exits clean.

---

## Step 7: Retiring a Node

When a client engagement ends, retire the node - do not delete it or reuse the address.

```bash
# Edit das.manifest.yaml directly to add deprecated: true
```

In `das.manifest.yaml`, find the node and add the flag:

```yaml
"02.02":
  label: Pinnacle-Health
  description: Pinnacle Health Systems - Indianapolis, IN
  type: category
  parent: "02"
  deprecated: true
```

The node stays in the manifest permanently. The address `02.02` is now retired and will
never be reused. The folder and its contents can be archived, but the manifest entry remains.

---

## Next Steps

- See [docs/concepts.md](concepts.md) for a deeper explanation of DAS addressing and the manifest
- See [docs/cli-reference.md](cli-reference.md) for the complete command reference
- See [docs/spec.md](spec.md) for the full Hexaxia DAS design specification
