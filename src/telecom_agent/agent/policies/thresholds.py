"""Confidence, retrieval-score and groundedness cut-offs in one place.

Gates read these constants; tests exercise behaviour at and around each cut-off.
"""

from __future__ import annotations

from dataclasses import dataclass

from telecom_agent.config.settings import Settings


@dataclass(frozen=True)
class Thresholds:
    clarify_confidence_floor: float = 0.60  # below → ask a clarifying question
    retrieval_score_floor: float = 0.35  # max(score) below → answer-not-found, escalate
    groundedness_floor: float = 0.75  # below → retry or escalate
    max_verify_attempts: int = 2  # retry budget for the verify loop

    @classmethod
    def from_settings(cls, s: Settings) -> Thresholds:
        return cls(
            clarify_confidence_floor=s.clarify_confidence_floor,
            retrieval_score_floor=s.retrieval_score_floor,
            groundedness_floor=s.groundedness_floor,
            max_verify_attempts=s.max_verify_attempts,
        )
