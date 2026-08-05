"""End-to-end eval: run the full graph over a mixed utterance set and report the
resolution mix, mean latency and mean token cost. Run with ``python -m evals.runners.run_e2e``.
"""

from __future__ import annotations

import time
from collections import Counter

from evals.loader import load_jsonl, write_report
from telecom_agent.api.deps import build_container
from telecom_agent.core.enums import Alias
from telecom_agent.core.types import TokenUsage
from telecom_agent.core.utils import new_session_id, new_trace_id
from telecom_agent.observability.cost import estimate_cost


def run(limit: int = 40) -> dict:
    container = build_container()
    rows = load_jsonl("classification")[:limit]

    outcomes: Counter[str] = Counter()
    latencies: list[float] = []
    costs: list[float] = []
    tokens: list[int] = []

    for row in rows:
        start = time.monotonic()
        final = container.graph.invoke(
            {
                "session_id": new_session_id(),
                "trace_id": new_trace_id(),
                "user_input": row["utterance"],
                "token_usage": TokenUsage(),
            }
        )
        latencies.append((time.monotonic() - start) * 1000)
        outcomes[str(final.get("resolution", "UNKNOWN"))] += 1
        usage = final.get("token_usage") or TokenUsage()
        provider = final.get("provider", container.settings.default_provider)
        tokens.append(usage.total)
        costs.append(estimate_cost(provider, Alias.CHAT_MAIN, usage))

    n = len(rows) or 1
    summary = {
        "provider": container.settings.default_provider.value,
        "n": len(rows),
        "resolution_mix": dict(outcomes),
        "mean_latency_ms": round(sum(latencies) / n, 1),
        "p95_latency_ms": round(sorted(latencies)[int(0.95 * (n - 1))], 1) if latencies else 0.0,
        "mean_tokens": round(sum(tokens) / n, 1),
        "mean_cost_usd": round(sum(costs) / n, 6),
    }
    lines = [
        "# End-to-end eval\n",
        f"- Provider: **{summary['provider']}**",
        f"- Cases: **{summary['n']}**",
        f"- Resolution mix: `{summary['resolution_mix']}`",
        f"- Mean latency: **{summary['mean_latency_ms']} ms**  ·  "
        f"p95: **{summary['p95_latency_ms']} ms**",
        f"- Mean tokens/turn: **{summary['mean_tokens']}**  ·  "
        f"mean est. cost/turn: **${summary['mean_cost_usd']}**",
    ]
    write_report("e2e", "\n".join(lines) + "\n")
    print(summary)
    return summary


if __name__ == "__main__":
    run()
