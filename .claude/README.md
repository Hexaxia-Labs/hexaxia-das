# DAS Agents and Skills

Project-local Claude Code agents and skills for the Hexaxia DAS project.

## Agents (`.claude/agents/`)

- **das-engineer** - AI/ML engineer for the `das` tool. Designs + implements retrieval/naming
  features with TDD, grounded in the closed benchmark findings; can run the nav-test harness.
- **das-operator** - intelligent archivist. Ingests, addresses, retrieves from, and audits
  real DAS corpora using the validated rag-nav pattern.

## Skills (`.claude/skills/`)

| Skill | Owner | Purpose |
|---|---|---|
| synapaxia-memory | shared | Recall/store episodes + procedures around every task |
| writing-passport-summaries | operator | Write the RAG-critical passport summary |
| corpus-ingest | operator | Add a document: address, type, filename, passport, tags |
| rag-nav-retrieval | operator | Validated rag-nav pattern with graceful fallbacks |
| corpus-audit | operator | Corpus health: validate, passports, tag hygiene |
| das-feature-tdd | engineer | The project's test-driven development loop |
| retrieval-design | engineer | Design retrieval features from benchmark evidence |
| embedding-eval | engineer | Validate ML changes against the nav-test harness |

synapaxia is used only as agent memory, never for document content. The operator's RAG path
requires Ollama + an embedded ChromaDB collection and degrades to manifest/filesystem nav.
