# Synthetic Knowledge Base

Everything under `data/kb/` is **synthetic**. There is no real customer, client, or
company data here — these are invented Indian-telecom style runbooks, FAQs and policies
authored purely to exercise retrieval and citation. (This file is named `README.md`, which
the loader deliberately skips, so it is never ingested.)

## How a document maps to a citation

Each `.md` file uses a strict two-line header the loader depends on:

```
doc_id: KB-101
# No Signal / No Service — First-Line Diagnostics
```

- `doc_id:` (line 1) is the stable id the agent cites, e.g. `[KB-101 §Steps]`.
- `# Title` (line 2) is the human-readable title shown in the citation card.
- Every `## Section Heading` starts a new **citable section**. The chunker
  (`telecom_agent.rag.chunking`) splits on these headings and stores the heading text as
  the citation `section`, so keep headings short and meaningful (`Overview`, `Steps`,
  `Escalation`, `Timelines`).

## Layout

| Folder | Style | Example |
|---|---|---|
| `runbooks/` | Step-by-step troubleshooting under a `## Steps` heading | APN reset, porting, KYC |
| `faq/` | Question-and-answer, one `##` per question | speed expectations, VoLTE |
| `policies/` | Policy statements (SLA, refunds, consent, KYC) | billing adjustment, FUP |

`faq/quick_answers.csv` demonstrates the CSV FAQ loader (`doc_id,question,answer`).

## Coverage

At least two documents exist for every one of the 12 `IssueCategory` values, so any
category the classifier picks has grounded material to retrieve. `manifest.yaml` lists
every `doc_id` with its title, owner, version, effective date and category.

## Rebuilding the index

The index is built from this folder by `make ingest` (or automatically on first startup
in dev). Nothing here needs re-embedding by teammates — the built index is published as a
release artifact.
