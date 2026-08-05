"""Groundedness eval: citation coverage on answered turns + escalation recall on the
must-escalate set. Provider-sensitive (the verifier is a model). Run with:
``python -m evals.runners.run_groundedness``.
"""

from __future__ import annotations

from evals.loader import load_jsonl, write_report
from evals.metrics import citation_coverage, escalation_recall
from telecom_agent.api.deps import build_container
from telecom_agent.core.enums import Resolution
from telecom_agent.core.types import TokenUsage
from telecom_agent.core.utils import new_session_id, new_trace_id


def _invoke(container, text: str) -> dict:
    return container.graph.invoke(
        {
            "session_id": new_session_id(),
            "trace_id": new_trace_id(),
            "user_input": text,
            "token_usage": TokenUsage(),
        }
    )


def run() -> dict:
    container = build_container()

    # citation coverage over golden_qa
    turns = []
    for row in load_jsonl("golden_qa"):
        final = _invoke(container, row["question"])
        answered = final.get("resolution") == Resolution.RESOLVED
        turns.append({"answered": answered, "has_citation": bool(final.get("citations"))})
    coverage = citation_coverage(turns)

    # escalation recall over the must-escalate set
    esc_results = []
    for row in load_jsonl("escalation"):
        final = _invoke(container, row["utterance"])
        esc_results.append(
            {
                "must_escalate": bool(row.get("must_escalate", True)),
                "escalated": final.get("resolution") == Resolution.ESCALATED,
            }
        )
    esc_recall = escalation_recall(esc_results)

    summary = {
        "provider": container.settings.default_provider.value,
        "citation_coverage": round(coverage, 3),
        "answered_turns": sum(1 for t in turns if t["answered"]),
        "escalation_recall": round(esc_recall, 3),
        "escalation_cases": len(esc_results),
    }
    lines = [
        "# Groundedness eval\n",
        f"- Provider: **{summary['provider']}**",
        f"- Citation coverage (answered turns cite a source): "
        f"**{summary['citation_coverage']}** (target ≥ 0.90)",
        f"- Answered turns: **{summary['answered_turns']}** / {len(turns)}",
        f"- Escalation recall (must-escalate set): "
        f"**{summary['escalation_recall']}** (target 1.00)",
    ]
    write_report("groundedness", "\n".join(lines) + "\n")
    print(summary)
    return summary


if __name__ == "__main__":
    run()
