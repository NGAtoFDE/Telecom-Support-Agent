"""Simulated outage check for a circle. Deterministic, synthetic — no real telemetry.

A P1 "no service in <circle>" turn can consult this to enrich the escalation summary the
NOC receives. Returns a stable verdict per circle so demos and tests reproduce.
"""

from __future__ import annotations

import hashlib

# A couple of circles are hard-coded as "known incident" for demo storytelling.
_KNOWN_INCIDENTS = {"pune", "maharashtra"}


def check_outage(circle: str | None) -> dict:
    if not circle:
        return {"circle": None, "outage_suspected": False, "detail": "no circle supplied"}
    key = circle.strip().lower()
    if key in _KNOWN_INCIDENTS:
        return {
            "circle": circle,
            "outage_suspected": True,
            "detail": f"Elevated fault reports in {circle}; NOC investigating (simulated).",
        }
    # Otherwise derive a stable pseudo-verdict so behaviour is reproducible.
    h = int(hashlib.sha256(key.encode()).hexdigest(), 16)
    suspected = h % 5 == 0
    return {
        "circle": circle,
        "outage_suspected": suspected,
        "detail": "Simulated diagnostics: "
        + ("degraded cell sites detected." if suspected else "no widespread fault detected."),
    }
