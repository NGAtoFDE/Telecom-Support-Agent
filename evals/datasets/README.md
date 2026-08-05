# Eval datasets

Frozen ground truth. Changes require a PR (README §8, §14). Four datasets, each owned:

| File | Metrics | Owner |
|---|---|---|
| `golden_qa.jsonl` | recall@5, precision@3, groundedness/citation coverage | M2 |
| `classification.jsonl` | accuracy, per-class F1, confusion matrix | M1 |
| `escalation.jsonl` | escalation recall (must be 1.00 for P1) | M3 |
| `adversarial.jsonl` | refusal / injection resistance | M5 |

## A note on `expected_doc_ids`

The `expected_doc_ids` in `golden_qa.jsonl` (e.g. `KB-114`) are **illustrative**. They are
written to line up with the synthetic KB's numbering scheme, but the authoritative doc ids
live in `data/kb/manifest.yaml`. If a retrieval eval reports lower recall than expected,
first confirm the referenced ids exist in the built index — `run_retrieval.py` prints how
many expected ids are actually present so a mismatch is obvious rather than silent.

Sync step (do this once the KB is finalised): open `data/kb/manifest.yaml`, and for each
golden question update `expected_doc_ids` to the real doc id(s) whose sections answer it.

## Enum values

`expected_category` / `expected_priority` use the exact string values from
`telecom_agent.core.enums` (`IssueCategory`, `Priority`). Any drift will show up as an
"unknown label" in the confusion matrix.
