"""Retrieval eval: recall@5 and precision@3 over golden_qa. Provider-independent — dense
+ BM25 are local. Run with: ``python -m evals.runners.run_retrieval``.
"""

from __future__ import annotations

from evals.loader import load_jsonl, write_report
from evals.metrics import precision_at_k, recall_at_k
from telecom_agent.api.deps import build_container


def run() -> dict:
    container = build_container()
    index_ids = {c.doc_id for c in container.retriever._store.chunks}
    rows = load_jsonl("golden_qa")

    recalls: list[float] = []
    precisions: list[float] = []
    expected_present = 0
    expected_total = 0

    per_case = []
    for row in rows:
        expected = row.get("expected_doc_ids", [])
        expected_total += len(expected)
        expected_present += sum(1 for d in expected if d in index_ids)

        res = container.retriever.search(row["question"], k=8)
        retrieved_ids = [c.doc_id for c in res.chunks]
        r5 = recall_at_k(retrieved_ids, expected, 5)
        p3 = precision_at_k(retrieved_ids, expected, 3)
        recalls.append(r5)
        precisions.append(p3)
        per_case.append(
            (row["id"], round(r5, 3), round(p3, 3), round(res.max_score, 3), retrieved_ids[:3])
        )

    summary = {
        "provider": container.settings.default_provider.value,
        "n": len(rows),
        "recall@5": round(sum(recalls) / len(recalls), 3) if recalls else 0.0,
        "precision@3": round(sum(precisions) / len(precisions), 3) if precisions else 0.0,
        "expected_ids_present": f"{expected_present}/{expected_total}",
    }

    lines = [
        "# Retrieval eval\n",
        f"- Provider: **{summary['provider']}**",
        f"- Cases: **{summary['n']}**",
        f"- recall@5: **{summary['recall@5']}**  (target ≥ 0.85)",
        f"- precision@3: **{summary['precision@3']}**",
        f"- expected doc_ids present in index: **{summary['expected_ids_present']}** "
        "(if low, sync golden_qa `expected_doc_ids` with data/kb/manifest.yaml)\n",
        "| id | recall@5 | precision@3 | top score | top-3 retrieved |",
        "|---|---|---|---|---|",
    ]
    for cid, r5, p3, ms, top in per_case:
        lines.append(f"| {cid} | {r5} | {p3} | {ms} | {', '.join(top)} |")
    write_report("retrieval", "\n".join(lines) + "\n")

    print(summary)
    return summary


if __name__ == "__main__":
    run()
