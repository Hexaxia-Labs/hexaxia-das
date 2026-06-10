# Writing Passport Summaries

**Date:** 2026-05-28  
**Author:** Aaron Lamb  
**Status:** Active - practical guide, update as corpus patterns evolve

The `summary` field in a Document Passport is the single highest-leverage thing you can improve for RAG routing accuracy. This guide explains what makes a summary good or bad, with examples from the test corpus.

> This guide covers the `summary` field specifically. For the full Document Passport
> reference (all fields, format, and lifecycle), see [passports.md](passports.md).

---

## Why the Summary Matters

When an agent runs a RAG pre-query, it embeds the user's question and searches the passport chunk collection. The passport chunk is:

```
[passport] {title} | type:{type} status:{status} address:{das_address}
{summary}
```

The summary is the body of this chunk. It is the only variable the RAG model has to route the query to the right DAS address. The title repeats the filename. The type and status are structural. The summary is the content.

A query like "what blockers exist on the NetBird deployment for ACME?" will route to the right document if and only if the summary for that document answers that question semantically. The model does not read the document - it only sees the summary.

**Benchmark confirmation:** mxbai-embed-large routed 7/8 questions correctly in the test corpus. The one miss (Q4: "list all active ACME projects") was traced to a weak passport summary on the ACME Projects folder - its summary did not enumerate the projects it contained. This caused the model to route to a tangentially related document. The summary is the entire signal.

---

## The Rule

**Write the summary to answer the questions agents will ask about this document - not to describe what the document is.**

This is the only rule. Everything else below is application of this rule.

---

## Good vs. Poor: Side by Side

### Direct lookup (Q1-class)

**Question an agent might ask:** "What blockers exist on the NetBird ZTNA deployment for ACME?"

**Poor:**
```
This document describes the deployment process for NetBird ZTNA at Acme Corp.
It covers installation, configuration, and troubleshooting steps.
```

**Good:**
```
Six-phase runbook to deploy NetBird ZTNA for Acme Corp (ACME). Current blockers:
firewall rules on ports 51820/UDP not yet approved by ACME IT, MFA enrollment pending for 3
admin accounts, and UAT sign-off deferred until May 30. Contact: Jay M. (ACME IT lead).
```

Why the good one works: it names the subject (NetBird ZTNA), the client (ACME), the document type (runbook), and the specific facts an agent would retrieve (blockers, port numbers, personnel, deadline). The poor one is accurate but generic - "deployment process" and "troubleshooting steps" could describe dozens of documents.

---

### Enumeration (Q4-class / D1-class)

**Question an agent might ask:** "List all active ACME projects."

**Poor (on the ACME Projects folder):**
```
Contains project documents for the Acme Corp client engagement.
```

**Good:**
```
ACME active projects (4): NetBird ZTNA deployment (02.01.04, runbook), security compliance
audit (02.01.06, report, Q3 target), staff onboarding automation (02.01.07, plan, draft),
and web portal redesign (02.01.09, spec, on hold). All project files live in 02.01-ACME/.
```

Why the good one works: it answers the enumeration question directly. The agent gets the list from the passport, skipping the need to ls four subdirectories and open four files. The poor one triggers a navigation cascade.

This is especially important for **folder-level passports** - index documents and category-level README files. These are the routing targets for enumeration queries. If their summaries don't enumerate what they contain, RAG will miss.

---

### Cross-area lookup (Q3-class)

**Question an agent might ask:** "What deliverables have been sent to Globex in the last 60 days?"

**Poor:**
```
Deliverable tracking for Globex. Includes proposals, reports, and other client documents.
```

**Good:**
```
Deliverable log for Globex (GBX) client engagement. Last 60 days: brand identity
proposal (02.02.05, delivered 260501), Q1 performance report (02.02.08, delivered 260415),
and social media content calendar (02.02.11, delivered 260418). Client contact: Maria V.
Engagement type: creative agency retainer.
```

Why the good one works: it answers the time-bounded question. The agent gets the answer from the RAG hit without reading the deliverable log at all. The poor one sends the agent to the right area but still requires file-open turns.

---

### Reference/structural (Q5/Q6-class)

**Question an agent might ask:** "What is the current NetBird pricing tier?" or "What types of documents exist in the 03-Business area?"

**Poor:**
```
Reference document on NetBird pricing and tier information.
```

**Good:**
```
NetBird pricing reference: Free tier (up to 5 peers), Team tier ($5/seat/mo, SSO + audit
logs), Business tier ($12/seat/mo, custom routing + API). Updated 260501. Source: NetBird
published pricing page. Note: trial includes Business features for 30 days.
```

**Poor (structural):**
```
Overview of the 03-Business area and its contents.
```

**Good (structural):**
```
Index for 03-Business: strategy docs (03.01-03.03), proposals (03.04-03.06), contracts
(03.07), vendor relations (03.08), and admin/compliance (03.09-03.10). Active: 12 strategy
docs, 4 open proposals, 8 executed contracts. Most recent: 03.07.02-TT-contract-shine-dist.md
(260518).
```

---

## Length and Format

**Target:** 2-5 sentences or 50-150 words. Long enough to answer the likely questions; short enough that the embedding model captures it without dilution.

**What to include:**

- Subject: what this document is about (not "this document is about X", just say X)
- Key entities: client name, product name, people, org codes
- Key facts: numbers, dates, statuses, amounts, counts
- Type context: if it's a runbook, what are the phases? If it's a report, what are the findings?
- Relationships: what other addresses does this touch? Who commissioned it?

**What to exclude:**

- Meta-commentary: "This document provides...", "Contains information about...", "Covers the topic of..."
- Generic filler: "Step-by-step guide", "Comprehensive overview", "Detailed analysis"
- Redundant context: the title already says the document name; the type field already says the type
- Future-tense hedging: "Will cover", "Is intended to describe" - if the document exists, it already does what it does

---

## Folder-Level Passports

Every folder with more than 3 documents should have an index document with a passport. The passport summary for that index should enumerate what the folder contains - not describe the folder's purpose in the abstract.

```markdown
<!--
passport:
  title: "02.01-ACME Active Projects Index"
  type: reference
  status: active
  tags: [ACME]
  das_address: "02.01"
  summary: "Active projects for Acme Corp: NetBird ZTNA (02.01.04, runbook,
            3 open blockers), security audit (02.01.06, Q3), onboarding automation
            (02.01.07, draft), portal redesign (02.01.09, on hold). Client contact:
            Jay M. Primary address: 02.01-ACME/."
-->
```

This one passport summary answers the Q4-class question ("list all active ACME projects") from RAG alone, with zero navigation turns.

---

## Testing Your Summary

Before filing a passport, ask: "If an agent embedded this summary and compared it against 30 other passports, would it pick this one for questions about [X]?"

Run the check:

1. Write the summary.
2. Identify the 2-3 most likely queries that should route here.
3. Read the summary and ask: does it contain the words and concepts that appear in those queries?
4. If not, add them.

The benchmark miss on Q4 (ACME active projects) is the clearest example of what happens when step 3 fails. The summary for `02.01-ACME` said something like "Acme Corp client folder" - it contains the word ACME but says nothing about projects or their statuses. The model routed to an unrelated content-calendar document instead because that document's summary mentioned "active posts" - which overlapped with "active projects" more than the ACME index did.

**Fix:** Name the specific projects and their statuses in the summary. Add counts. The model routes on semantic proximity - give it the right words.

---

## Quick Reference

| Do | Don't |
|---|---|
| Name the subject directly | "This document describes..." |
| Include counts and statuses | Generic "comprehensive guide" |
| Enumerate contained items (for indexes) | "Contains information about X" |
| Name specific people, org codes, dates | Vague "recent" or "current" |
| Match the vocabulary of likely queries | Paraphrase using different terms |
| State current facts (blockers, statuses, amounts) | Future tense / hedged language |
| 2-5 sentences or 50-150 words | > 300 words (dilutes signal) |

---

## Format Reference

Full passport block format:

```markdown
<!--
passport:
  title: "Document title - specific enough to appear in search"
  type: runbook           # controlled vocabulary - see spec §5.4
  status: active          # active | draft | deprecated | archived
  tags: [ACME, NETBIRD]    # from corpus vocabulary in das.config.yaml
  das_address: "02.01.04"
  created: "2026-05-09"
  modified: "2026-05-28"
  summary: "2-5 sentences. Name subject, type, key entities, current facts.
            Answer the questions agents will ask - not what the document is.
            This field alone determines RAG routing accuracy."
-->
```

The `summary` field is the only field that drives RAG retrieval. All other fields are structural metadata. Write the summary last, after you know what questions the document needs to answer.
