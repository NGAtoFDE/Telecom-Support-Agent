"""Routing table invariants: every P1 → NOC_L2; billing disputes → BILLING_OPS."""

from __future__ import annotations

import pytest

from telecom_agent.agent.policies.routing import route
from telecom_agent.core.enums import EscalationQueue as Q
from telecom_agent.core.enums import IssueCategory as C
from telecom_agent.core.enums import Priority as P


@pytest.mark.parametrize("category", list(C))
def test_every_p1_routes_to_noc(category):
    assert route(category, P.P1) == Q.NOC_L2


def test_billing_dispute_routes_to_billing_ops():
    for pri in (P.P2, P.P3, P.P4):
        assert route(C.BILLING_DISPUTE, pri) == Q.BILLING_OPS


@pytest.mark.parametrize(
    "category,expected",
    [
        (C.SIM_ACTIVATION, Q.SIM_PROVISIONING),
        (C.SIM_SWAP_PORTING, Q.SIM_PROVISIONING),
        (C.ROAMING, Q.ROAMING_PARTNER_DESK),
        (C.RECHARGE_PAYMENT_FAILED, Q.BILLING_OPS),
        (C.DEVICE_CONFIG, Q.GENERAL_L1),
        (C.ACCOUNT_KYC, Q.GENERAL_L1),
        (C.OTHER, Q.GENERAL_L1),
        (C.NETWORK_COVERAGE, Q.NOC_L2),
    ],
)
def test_category_defaults_non_p1(category, expected):
    assert route(category, P.P3) == expected
