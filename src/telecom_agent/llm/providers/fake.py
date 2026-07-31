"""Deterministic, credential-free provider.

This is the single most important reliability asset in the project (README §9): it ships
on Day 1 morning so nobody is blocked on a real model, and it guarantees the demo runs
offline. It inspects the conversation and returns *plausible, structured* responses that
satisfy the same Pydantic contracts the real providers must satisfy.

It is intentionally rule-based, not random, so tests and evals are reproducible.
"""

from __future__ import annotations

import hashlib
import json
import re

from telecom_agent.core.enums import Alias, IssueCategory, Priority, Provider
from telecom_agent.core.types import Message, TokenUsage
from telecom_agent.llm.base import ChatResult

# Common English function words, dropped from the pseudo-embedding feature space so they
# don't create spurious similarity between unrelated texts.
_STOPWORDS = frozenset(
    [
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "been",
        "but",
        "by",
        "did",
        "do",
        "does",
        "for",
        "from",
        "had",
        "has",
        "have",
        "how",
        "i",
        "if",
        "in",
        "into",
        "is",
        "it",
        "its",
        "my",
        "no",
        "not",
        "of",
        "on",
        "or",
        "so",
        "that",
        "the",
        "their",
        "them",
        "then",
        "there",
        "this",
        "to",
        "was",
        "were",
        "what",
        "when",
        "where",
        "which",
        "who",
        "will",
        "with",
        "you",
        "your",
        "me",
        "not",
        "don",
        "t",
        "am",
        "pm",
    ]
)

# Keyword → (category, priority). First match wins; order matters (specific first).
_RULES: list[tuple[re.Pattern[str], IssueCategory, Priority]] = [
    (
        re.compile(r"\b(no service|outage|down for everyone|tower)\b", re.I),
        IssueCategory.NETWORK_COVERAGE,
        Priority.P1,
    ),
    (
        re.compile(r"\b(no data|no internet|no signal)\b", re.I),
        IssueCategory.NETWORK_COVERAGE,
        Priority.P1,
    ),
    (re.compile(r"\b(slow|buffering|speed|throttl)\b", re.I), IssueCategory.DATA_SLOW, Priority.P2),
    (
        re.compile(r"\b(call drop|dropped call|disconnect)\b", re.I),
        IssueCategory.CALL_DROP,
        Priority.P2,
    ),
    (
        re.compile(r"\b(overcharg|wrong bill|refund|dispute|double charge)\b", re.I),
        IssueCategory.BILLING_DISPUTE,
        Priority.P3,
    ),
    (
        re.compile(r"\b(recharge|payment failed|top ?up|money deducted)\b", re.I),
        IssueCategory.RECHARGE_PAYMENT_FAILED,
        Priority.P3,
    ),
    (re.compile(r"\b(activat|new sim)\b", re.I), IssueCategory.SIM_ACTIVATION, Priority.P3),
    (
        re.compile(r"\b(port|mnp|swap sim|sim swap)\b", re.I),
        IssueCategory.SIM_SWAP_PORTING,
        Priority.P3,
    ),
    (re.compile(r"\b(roaming|abroad|international)\b", re.I), IssueCategory.ROAMING, Priority.P3),
    (
        re.compile(r"\b(subscription|vas|caller tune|pack activated)\b", re.I),
        IssueCategory.VAS_SUBSCRIPTION,
        Priority.P3,
    ),
    (
        re.compile(r"\b(apn|hotspot|tether|settings)\b", re.I),
        IssueCategory.DEVICE_CONFIG,
        Priority.P2,
    ),
    (
        re.compile(r"\b(kyc|aadhaar|document|verification)\b", re.I),
        IssueCategory.ACCOUNT_KYC,
        Priority.P3,
    ),
]


def _last_user_text(messages: list[Message]) -> str:
    for m in reversed(messages):
        if m.role == "user":
            return m.content
    return messages[-1].content if messages else ""


def _stable_confidence(text: str) -> float:
    """Deterministic pseudo-confidence in [0.55, 0.95] derived from the text hash."""
    h = int(hashlib.sha256(text.encode()).hexdigest(), 16)
    return round(0.55 + (h % 41) / 100.0, 2)


def _classify(text: str) -> tuple[IssueCategory, Priority, float]:
    for pattern, cat, pri in _RULES:
        if pattern.search(text):
            return cat, pri, max(0.62, _stable_confidence(text))
    return IssueCategory.OTHER, Priority.P4, 0.5


class FakeProvider:
    name = Provider.FAKE

    def __init__(self, dim: int = 1024) -> None:
        self._dim = dim

    # -- chat ---------------------------------------------------------------
    def chat(
        self,
        messages: list[Message],
        *,
        alias: Alias,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        json_mode: bool = False,
    ) -> ChatResult:
        user = _last_user_text(messages)
        system = " ".join(m.content for m in messages if m.role == "system").lower()
        prompt_tokens = sum(len(m.content) // 4 for m in messages)

        # The system prompt tells us which node is calling. We branch on that so the
        # fake output always satisfies the caller's Pydantic schema.
        if "classifier" in system or "classify" in system:
            cat, pri, conf = _classify(user)
            body = json.dumps(
                {
                    "category": cat.value,
                    "priority": pri.value,
                    "confidence": conf,
                    "entities": self._entities(user),
                }
            )
        elif "verifier" in system or "groundedness" in system:
            body = json.dumps({"groundedness": 0.93, "supported": True, "unsupported_claims": []})
        elif "clarify" in system:
            body = (
                "Could you tell me your circle (city/region) and whether this is "
                "prepaid or postpaid?"
            )
        else:  # answer generation
            body = self._fake_answer(messages)

        return ChatResult(
            text=body,
            usage=TokenUsage(prompt_tokens=prompt_tokens, completion_tokens=len(body) // 4),
            model=f"fake-{alias.value}",
            provider=Provider.FAKE,
        )

    @staticmethod
    def _entities(text: str) -> dict:
        entities: dict = {}
        circle = re.search(
            r"\b(pune|mumbai|delhi|bangalore|chennai|kolkata|maharashtra)\b", text, re.I
        )
        if circle:
            entities["circle"] = circle.group(0).title()
        amount = re.search(r"(?:rs\.?|inr|₹)\s?(\d+)", text, re.I)
        if amount:
            entities["amount"] = int(amount.group(1))
        return entities

    @staticmethod
    def _fake_answer(messages: list[Message]) -> str:
        """Produce a grounded-looking answer that cites whatever chunk ids appear in the
        context block the draft node passed in (keeps the verifier happy in fake mode)."""
        context = "\n".join(m.content for m in messages if m.role != "assistant")
        ids = re.findall(r"\b(KB-\d+)\b", context)
        cite = f" [{ids[0]} §1]" if ids else " [KB-000 §1]"
        return (
            "Here are the steps to resolve this:\n"
            "1. Toggle airplane mode for 10 seconds, then retry.\n"
            "2. Reset your APN to the operator default and reboot.\n"
            "3. If the issue persists, note the time and we will escalate." + cite
        )

    # -- embeddings ---------------------------------------------------------
    def embed(self, texts: list[str], *, alias: Alias = Alias.EMBED) -> list[list[float]]:
        """Deterministic hash-based pseudo-embeddings. Not semantically meaningful, but
        stable and offline — enough to exercise the FAISS path without Azure."""
        return [self._embed_one(t) for t in texts]

    def _embed_one(self, text: str) -> list[float]:
        # Feature space = content unigrams (stopwords dropped) + adjacent bigrams, hashed
        # into a wide vector. Dropping stopwords and adding bigrams keeps unrelated texts
        # near-orthogonal, so cosine reflects real overlap and the retrieval floor is
        # meaningful even offline. (A production embedder would replace this entirely.)
        vec = [0.0] * self._dim
        for tok in self._features(text):
            h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
            vec[h % self._dim] += 1.0
        norm = sum(v * v for v in vec) ** 0.5 or 1.0
        return [v / norm for v in vec]

    @staticmethod
    def _features(text: str) -> list[str]:
        words = [
            w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) >= 3 and w not in _STOPWORDS
        ]
        bigrams = [f"{a}_{b}" for a, b in zip(words, words[1:], strict=False)]
        return words + bigrams

    def health(self) -> bool:
        return True
