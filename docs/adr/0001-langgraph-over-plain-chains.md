# ADR 0001 — LangGraph over plain chains

Status: Accepted

## Context

The triage workflow is not linear. It has conditional exits (low confidence → clarify; P1 →
escalate; empty retrieval → escalate) and a cycle (verify → retrieve retry, up to a bounded
number of attempts). A plain sequential chain models none of these cleanly; you end up with
imperative `if/else` scattered across a monolith, and the retry loop becomes hand-rolled
recursion that is hard to bound and hard to trace.

## Decision

Use LangGraph. Model the workflow as a state machine over a single `TriageState` TypedDict.
Nodes are one-per-file functions returning partial state updates; edges are pure
`state -> next` functions in `agent/edges.py`; the graph is assembled in `agent/graph.py`.
Decision thresholds live in `agent/policies/` so branching is data, not code buried in nodes.

## Consequences

- Conditional exits and the bounded verify→retrieve cycle are first-class and testable
  (`tests/unit/test_thresholds.py`, `tests/integration/test_graph_paths.py`).
- One-node-per-file means five engineers add nodes without colliding; only `graph.py` wires
  edges, so merge conflicts concentrate in one small, rarely-changed file.
- Per-node spans and token accounting fall out naturally, which the observability story needs.
- Slight learning-curve cost and a dependency on LangGraph's compile/invoke model.

## Alternatives considered

- **Plain LangChain LCEL chain** — rejected: no clean cycle or conditional-exit primitive.
- **Hand-rolled orchestrator** — rejected: we would reinvent state, retries and tracing, and
  spend the 7 days on plumbing instead of the AI path.
