"""(category, priority) → escalation queue, as a declarative table.

Adding or re-routing a queue must not require touching the graph (README §3.3). Routing
is pure data plus a tiny resolver, which is what makes the routing unit test meaningful.

Policy invariants encoded here (README §16):
- Every P1 routes to NOC_L2 (human review for high-risk, regardless of confidence).
- Every billing dispute routes to BILLING_OPS (a human owns money decisions).
"""

from __future__ import annotations

from telecom_agent.core.enums import EscalationQueue as Q
from telecom_agent.core.enums import IssueCategory as C
from telecom_agent.core.enums import Priority as P

# Category → default queue. Priority overrides below take precedence.
_CATEGORY_QUEUE: dict[C, Q] = {
    C.NETWORK_COVERAGE: Q.NOC_L2,
    C.DATA_SLOW: Q.NOC_L2,
    C.CALL_DROP: Q.NOC_L2,
    C.BILLING_DISPUTE: Q.BILLING_OPS,
    C.RECHARGE_PAYMENT_FAILED: Q.BILLING_OPS,
    C.SIM_ACTIVATION: Q.SIM_PROVISIONING,
    C.SIM_SWAP_PORTING: Q.SIM_PROVISIONING,
    C.ROAMING: Q.ROAMING_PARTNER_DESK,
    C.VAS_SUBSCRIPTION: Q.BILLING_OPS,
    C.DEVICE_CONFIG: Q.GENERAL_L1,
    C.ACCOUNT_KYC: Q.GENERAL_L1,
    C.OTHER: Q.GENERAL_L1,
}


def route(category: C, priority: P) -> Q:
    # Priority overrides first — these are the human-review guarantees.
    if priority == P.P1:
        return Q.NOC_L2
    if category == C.BILLING_DISPUTE:
        return Q.BILLING_OPS
    return _CATEGORY_QUEUE.get(category, Q.GENERAL_L1)
