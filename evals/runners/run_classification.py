"""Classification eval: accuracy, per-class F1, confusion matrix. Runs the classify node
directly against the configured provider. Run: ``python -m evals.runners.run_classification``.
"""

from __future__ import annotations

from evals.loader import load_jsonl, write_report
from evals.metrics import accuracy, confusion_matrix, per_class_f1
from telecom_agent.agent.nodes.classify import classify as classify_node
from telecom_agent.api.deps import build_container
from telecom_agent.core.enums import IssueCategory
from telecom_agent.core.types import TokenUsage
from telecom_agent.core.utils import new_session_id, new_trace_id


def run() -> dict:
    container = build_container()
    rows = load_jsonl("classification")

    cat_true, cat_pred, pri_true, pri_pred = [], [], [], []
    for row in rows:
        state = {
            "session_id": new_session_id(),
            "trace_id": new_trace_id(),
            "user_input": row["utterance"],
            "token_usage": TokenUsage(),
        }
        try:
            out = classify_node(state, container.agent_deps)
            cat_pred.append(out["category"].value)
            pri_pred.append(out["priority"].value)
        except Exception as exc:  # noqa: BLE001 - a crash counts as a wrong prediction
            print(f"[warn] {row['id']} failed: {exc}")
            cat_pred.append("OTHER")
            pri_pred.append("P4")
        cat_true.append(row["expected_category"])
        pri_true.append(row["expected_priority"])

    labels = [c.value for c in IssueCategory]
    cat_acc = accuracy(cat_true, cat_pred)
    pri_acc = accuracy(pri_true, pri_pred)
    f1 = per_class_f1(cat_true, cat_pred, labels)
    cm = confusion_matrix(cat_true, cat_pred, labels)

    summary = {
        "provider": container.settings.default_provider.value,
        "n": len(rows),
        "category_accuracy": round(cat_acc, 3),
        "priority_accuracy": round(pri_acc, 3),
        "macro_f1": f1["macro_f1"],
    }

    lines = [
        "# Classification eval\n",
        f"- Provider: **{summary['provider']}**",
        f"- Cases: **{summary['n']}**",
        f"- category accuracy: **{summary['category_accuracy']}** (target ≥ 0.90)",
        f"- priority accuracy: **{summary['priority_accuracy']}** (target ≥ 0.85)",
        f"- macro F1: **{summary['macro_f1']}**\n",
        "## Per-class F1",
        "| class | precision | recall | f1 | support |",
        "|---|---|---|---|---|",
    ]
    for lab in labels:
        m = f1[lab]
        lines.append(f"| {lab} | {m['precision']} | {m['recall']} | {m['f1']} | {m['support']} |")

    lines += ["\n## Confusion matrix (rows = true, cols = predicted)", ""]
    header = "| true \\ pred | " + " | ".join(labels) + " |"
    lines.append(header)
    lines.append("|" + "---|" * (len(labels) + 1))
    for t in labels:
        row_counts = [str(cm.get(t, {}).get(p, 0)) for p in labels]
        lines.append(f"| {t} | " + " | ".join(row_counts) + " |")

    write_report("classification", "\n".join(lines) + "\n")
    print(summary)
    return summary


if __name__ == "__main__":
    run()
