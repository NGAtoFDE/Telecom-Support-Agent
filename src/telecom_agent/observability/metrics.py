"""Prometheus metrics (also shipped to App Insights). Names mirror README §15 exactly.

All metrics are module-level singletons so any layer can import and increment them without
threading a registry through call sites.
"""

from __future__ import annotations

from prometheus_client import Counter, Histogram

turns_total = Counter("turns_total", "Triage turns handled", ["category", "priority"])
resolution_total = Counter("resolution_total", "Turn outcomes", ["outcome"])
escalations_total = Counter("escalations_total", "Escalations by queue", ["queue"])
turn_latency_seconds = Histogram("turn_latency_seconds", "End-to-end turn latency", ["provider"])
llm_failover_total = Counter(
    "llm_failover_total", "Failovers from primary to backup provider", ["reason"]
)
llm_errors_total = Counter("llm_errors_total", "LLM errors", ["provider", "kind"])
retrieval_score = Histogram(
    "retrieval_score",
    "Top retrieval score per turn",
    buckets=[0.0, 0.1, 0.2, 0.3, 0.35, 0.5, 0.7, 0.85, 1.0],
)
groundedness_score = Histogram(
    "groundedness_score",
    "Verifier groundedness per turn",
    ["provider"],
    buckets=[0.0, 0.5, 0.7, 0.8, 0.9, 0.95, 1.0],
)
llm_tokens_total = Counter("llm_tokens_total", "Tokens consumed", ["node", "provider"])


def record_failover(reason: str = "unknown") -> None:
    llm_failover_total.labels(reason=reason).inc()
