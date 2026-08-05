# Runbook

On-call reference: symptom → checks → remediation. Metric names are the Prometheus series
defined in `observability/metrics.py`; they are also shipped to Application Insights.

## Metrics reference

| Metric | Type | Meaning |
|---|---|---|
| `turns_total{category,priority}` | counter | volume mix |
| `resolution_total{outcome}` | counter | resolve vs clarify vs escalate |
| `escalations_total{queue}` | counter | queue load |
| `turn_latency_seconds{provider}` | histogram | p50/p95/p99 per provider |
| `llm_failover_total{reason}` | counter | how often / why we left the primary |
| `llm_errors_total{provider,kind}` | counter | timeouts, 429s, filter blocks, schema failures |
| `retrieval_score` | histogram | top retrieval score per turn |
| `groundedness_score{provider}` | histogram | hallucination early warning |
| `llm_tokens_total{node,provider}` | counter | cost attribution per node |

## Symptom → check → remediation

| Symptom | Check | Remediation |
|---|---|---|
| All turns escalate | `retrieval_score` histogram skewed low | KB coverage gap — add docs, re-`make ingest`, republish index |
| Latency p95 breached | `turn_latency_seconds{provider}` | check retry storms in `llm_errors_total` |
| `/readyz` returns 503 | its `checks` body | index missing → `make ingest`; DB not writable → check Azure Files mount; provider down → check keys |
| Duplicate tickets | `tickets` table | should be impossible (idempotency key); check clock skew across replicas |

## KQL queries (App Insights)

Escalation rate over the last hour:

```kql
customMetrics
| where name == "escalations_total"
| where timestamp > ago(1h)
| summarize escalations = sum(value)
```

p95 latency split by provider:

```kql
customMetrics
| where name == "turn_latency_seconds"
| extend provider = tostring(customDimensions.provider)
| summarize p95 = percentile(value, 95) by provider, bin(timestamp, 5m)
```

Every turn where groundedness < 0.8 (the "show me the bad answers" query):

```kql
traces
| where message == "verified"
| extend g = todouble(customDimensions.groundedness), trace_id = tostring(customDimensions.trace_id)
| where g < 0.8
| project timestamp, trace_id, g
| order by timestamp desc
```

