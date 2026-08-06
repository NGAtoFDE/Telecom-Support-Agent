"""Seeded, reproducible generator for synthetic customers and sample utterances.

Everything here is fabricated. No real customer, subscriber or account data is used or
produced. Run it to (re)generate ``customers.json`` and preview sample utterances:

    python data/synthetic/generator.py
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from telecom_agent.core.enums import IssueCategory

SEED = 42
_HERE = Path(__file__).parent

CIRCLES = [
    "Maharashtra", "Delhi", "Karnataka", "Tamil Nadu", "West Bengal",
    "Gujarat", "Kerala", "Punjab", "Rajasthan", "Uttar Pradesh (East)",
]
PLANS = ["Smart 299", "Unlimited 499", "Data Max 719", "Value 199", "Postpaid 999"]
DEVICES = ["Android (Samsung)", "Android (Xiaomi)", "iPhone 14", "iPhone 15",
           "Android (Vivo)", "Feature phone"]
ACCOUNT_TYPES = ["prepaid", "postpaid"]

# A couple of illustrative utterance templates per category (synthetic).
UTTERANCES: dict[IssueCategory, list[str]] = {
    IssueCategory.NETWORK_COVERAGE: [
        "No signal at all at home since this morning in {circle}",
        "Complete outage, my phone shows no service in {circle}",
    ],
    IssueCategory.DATA_SLOW: [
        "My mobile internet is very slow and keeps buffering",
        "4G data speed dropped to almost nothing today",
    ],
    IssueCategory.CALL_DROP: [
        "My calls keep dropping after a few seconds",
        "Frequent call drops whenever I move indoors",
    ],
    IssueCategory.BILLING_DISPUTE: [
        "I was charged twice on my last postpaid bill",
        "There is a wrong charge of Rs 199 I did not authorise",
    ],
    IssueCategory.RECHARGE_PAYMENT_FAILED: [
        "Recharge failed but money got deducted from my account",
        "My top-up of Rs 299 did not reflect but payment went through",
    ],
    IssueCategory.SIM_ACTIVATION: [
        "How long does a new SIM take to activate",
        "My new SIM is still not activated after a day",
    ],
    IssueCategory.SIM_SWAP_PORTING: [
        "I want to port my number to your network",
        "My SIM swap request is still pending",
    ],
    IssueCategory.ROAMING: [
        "I am travelling abroad, how do I activate international roaming",
        "No network on my phone while roaming overseas",
    ],
    IssueCategory.VAS_SUBSCRIPTION: [
        "A caller tune pack got activated without my consent, please refund",
        "How do I deactivate a VAS subscription",
    ],
    IssueCategory.DEVICE_CONFIG: [
        "My hotspot / tethering is not working",
        "How do I set the correct APN on my Android phone",
    ],
    IssueCategory.ACCOUNT_KYC: [
        "I need to re-verify my KYC with Aadhaar",
        "My connection is barred pending KYC verification",
    ],
    IssueCategory.OTHER: [
        "I have a general question about your services",
        "Where is the nearest store",
    ],
}


def make_customers(n: int = 20, seed: int = SEED) -> list[dict]:
    rng = random.Random(seed)
    out = []
    for i in range(1, n + 1):
        out.append(
            {
                "customer_id": f"CUST-{i:04d}",
                "circle": rng.choice(CIRCLES),
                "plan": rng.choice(PLANS),
                "device": rng.choice(DEVICES),
                "account_type": rng.choice(ACCOUNT_TYPES),
            }
        )
    return out


def sample_utterances(seed: int = SEED) -> list[dict]:
    rng = random.Random(seed + 1)
    rows = []
    for cat, templates in UTTERANCES.items():
        t = rng.choice(templates)
        rows.append({"category": cat.value, "utterance": t.format(circle=rng.choice(CIRCLES))})
    return rows


def main() -> None:
    customers = make_customers()
    (_HERE / "customers.json").write_text(
        json.dumps(customers, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"wrote {len(customers)} synthetic customers -> customers.json")
    print("\nSample synthetic utterances (one per category):")
    for row in sample_utterances():
        print(f"  [{row['category']:<24}] {row['utterance']}")


if __name__ == "__main__":
    main()
