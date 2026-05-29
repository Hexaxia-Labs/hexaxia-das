---
name: corpus-ingest
description: Use when adding a document to a DAS corpus - assign its address, pick the controlled type slug, name the file, write the passport block, apply tags selectively, and register the node. Triggers on "add a document", "ingest this", "file this doc", "where does this go", "give this an address".
---

# corpus-ingest

Add a document to a DAS corpus correctly the first time. Order matters: decide the
address, then the type, then the filename, then the passport, then register the node.

## Steps

1. **Find the right address.** Read `das.manifest.yaml` (or run `.venv/bin/das ls`) to see
   the existing tree. Pick the deepest existing parent the document belongs under. If a new
   folder address is needed, choose the next free `.NN` under that parent.

2. **Register the node if the address is new** (folders only):
   `.venv/bin/das add <address> <Label> "<one-sentence description>" [--agent-hint "..."]`
   Note: `das add` only writes the manifest node. It does NOT place the file or write the
   passport - those are steps 3-5.

3. **Pick the type slug** from the hard-capped vocabulary (spec 5.4):
   `runbook, plan, spec, design, strategy, playbook, proposal, contract, report, catalog,
   lead, post, template, reference, procedure`. If nothing fits, stop and ask - do not
   invent a type. New types require a spec change.

4. **Name the file** `{address}-{type}-{descriptor}.ext`. Keep the descriptor specific
   enough to carry search signal (avoid over-truncating words that appear in likely
   queries). The folder address prefix is not required on the file's folder - the filename
   carries the jump-table signal (benchmark finding 11).

5. **Write the passport block** at the top of the file (Markdown HTML comment). Delegate the
   `summary` field to the `writing-passport-summaries` skill - it is the RAG signal.
   ```markdown
   <!--
   passport:
     title: "Specific title that would appear in search"
     type: runbook
     status: active        # active | draft | deprecated | archived
     tags: [uls]           # see step 6 - selective only
     das_address: "02.01.04"
     created: "YYYY-MM-DD"
     modified: "YYYY-MM-DD"
     summary: "2-5 sentences answering the questions agents will ask. See the
               writing-passport-summaries skill."
   -->
   ```

6. **Apply tags selectively** (spec 5.3 Rule 6 / naming-convention-analysis). Tag only
   client- or market-scoped, out-of-context documents that surface in git log, search
   results, tickets, or email. Do NOT tag internal admin/product/marketing docs - tags add
   parsing cost to every `ls` of the folder (benchmark finding 10). Use the corpus tag
   vocabulary from `das.config.yaml`.

7. **Update folder-level index passport** if this folder now has more than 3 documents and
   the index summary no longer enumerates contents. Re-run `writing-passport-summaries`.

8. **Validate:** `.venv/bin/das validate`. Resolve any errors before finishing.
