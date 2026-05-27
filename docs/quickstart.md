# Quickstart: Building Your First JDX Corpus

This guide walks you through initializing a JDX corpus, building out an address tree,
naming files correctly, and validating your corpus.

We'll use a fictional company called **Atlas Technologies** as the example. Atlas has:
- Multiple clients
- Internal admin and finance docs
- A marketing team

**Time to complete:** About 10 minutes.

---

## Prerequisites

Install JDX:

```bash
python3 -m venv .venv
.venv/bin/pip install -e ~/Projects/jdx
# or once published to PyPI:
# .venv/bin/pip install jdx
```

Verify the install:

```bash
.venv/bin/jdx --help
```

---

## Step 1: Initialize the Corpus

Create a directory for your corpus and initialize it:

```bash
mkdir ~/Documents/atlas-corpus
cd ~/Documents/atlas-corpus
jdx init atlas-technologies --org ATL --context-type client --date-format YYMMDD
```

This creates two files:

```
atlas-corpus/
  jdx.config.yaml
  jdx.manifest.yaml
```

`jdx.config.yaml` defines the naming schema. It is permanent - do not edit it after
documents exist. Verify it looks right:

```yaml
version: '1.0'
corpus: atlas-technologies
initialized: 2026-05-27
address_separator: .
manifest: jdx.manifest.yaml
org: ATL
context_type: client
date_format: YYMMDD
```

---

## Step 2: Build the Address Tree

Add nodes parent-first. A node cannot be added before its parent exists.

**Add the top-level areas:**

```bash
jdx add 00 Admin "Company governance - legal, compliance, registrations"
jdx add 01 Finance "Accounting, invoicing, taxes, banking"
jdx add 02 Clients "One subfolder per active client engagement"
jdx add 03 HR "Hiring, onboarding, policies, team"
jdx add 04 Marketing "Brand, campaigns, content, SEO"
```

**Add categories under Admin:**

```bash
jdx add 00.01 Business-Registration "Incorporation certificates, jurisdiction filings"
jdx add 00.02 Insurance "Business liability and professional indemnity policies"
jdx add 00.03 Compliance "Regulatory compliance documents and audits"
```

**Add categories under Clients:**

```bash
jdx add 02.01 Northstar-Logistics "Northstar Logistics - Chicago, IL"
jdx add 02.02 Pinnacle-Health "Pinnacle Health Systems - Indianapolis, IN"
```

**Add subcategories under 02.01:**

```bash
jdx add 02.01.01 Contracts "MSA, SOWs, amendments"
jdx add 02.01.02 Correspondence "Emails, meeting notes, call logs"
jdx add 02.01.03 Projects "Active project deliverables"
```

---

## Step 3: Inspect the Manifest

List all nodes to see your address tree:

```bash
jdx ls
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
jdx ls 02
```

Search for anything related to contracts:

```bash
jdx find contract
```

---

## Step 4: Create the Folder Structure

Create folders using the JDX naming convention: `{address}-{Title-Cased-Label}/`

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

Files follow this pattern:

```
{address}-[{ORG}-][{CONTEXT}-]{descriptor}[-{YYMMDD}].ext
```

For Atlas Technologies with `org: ATL` and `context_type: client`:

```bash
# Articles of incorporation (no client context - internal doc)
touch 00-Admin/00.01-Business-Registration/00.01-ATL-articles-of-incorporation-260115.pdf

# MSA for Northstar Logistics
touch 02-Clients/02.01-Northstar-Logistics/02.01.01-Contracts/02.01.01-ATL-NSL-msa-260301.pdf

# SOW for a Northstar project
touch 02-Clients/02.01-Northstar-Logistics/02.01.01-Contracts/02.01.01-ATL-NSL-sow-security-audit-260415.pdf

# A project deliverable (no date needed)
touch 02-Clients/02.01-Northstar-Logistics/02.01.03-Projects/02.01.03-ATL-NSL-network-diagram.pdf
```

Naming breakdown for `02.01.01-ATL-NSL-msa-260301.pdf`:

| Component | Value | Source |
|---|---|---|
| Address | `02.01.01` | The containing folder's address |
| ORG | `ATL` | `org` field in jdx.config.yaml |
| CONTEXT | `NSL` | Short code for the client (Northstar Logistics) |
| Descriptor | `msa` | What the document is |
| Date | `260301` | YYMMDD - March 1, 2026 |

The CONTEXT code is optional even when `context_type` is configured. Omit it for
internal documents that do not belong to a specific client, project, or department.

---

## Step 6: Validate the Corpus

Run the validator to check that all folders and files follow the naming convention:

```bash
jdx validate
```

If everything is clean:

```
Corpus is valid.
```

If there are issues, the validator tells you what is wrong and where:

```
2 validation error(s):
  02-Clients/02.01-northstar-logistics: Folder label must be Title-Cased and hyphenated (e.g. '00-Admin')
  02-Clients/02.01-Northstar-Logistics/invoice.pdf: No JDX address prefix found
```

Fix the issues and run `jdx validate` again until it exits clean.

---

## Step 7: Retiring a Node

When a client engagement ends, retire the node - do not delete it or reuse the address.

```bash
# Edit jdx.manifest.yaml directly to add deprecated: true
```

In `jdx.manifest.yaml`, find the node and add the flag:

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

- See [docs/concepts.md](concepts.md) for a deeper explanation of JDX addressing and the manifest
- See [docs/cli-reference.md](cli-reference.md) for the complete command reference
- See [docs/spec.md](spec.md) for the full JDX design specification
