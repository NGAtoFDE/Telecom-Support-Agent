"""Small, dependency-light helpers: ids, hashing, time, text normalisation.

Deterministic where it can be, so tests and evals reproduce.
"""

from __future__ import annotations

import hashlib
import re
import uuid
from datetime import datetime, timezone


def new_trace_id() -> str:
    """A sortable-ish, URL-safe id for correlating logs, spans and DB rows."""
    return uuid.uuid4().hex


def new_session_id() -> str:
    return "sess_" + uuid.uuid4().hex[:8]


def new_ticket_id() -> str:
    return "TKT-" + uuid.uuid4().hex[:10].upper()


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def hour_bucket(ts: datetime | None = None) -> str:
    ts = ts or datetime.now(timezone.utc)
    return ts.strftime("%Y%m%d%H")


def idempotency_key(session_id: str, category: str, bucket: str | None = None) -> str:
    """sha256(session_id + category + hour_bucket) — dedupes ticket creation on retry."""
    bucket = bucket or hour_bucket()
    raw = f"{session_id}|{category}|{bucket}".encode()
    return hashlib.sha256(raw).hexdigest()


_WS = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    return _WS.sub(" ", text or "").strip()


def approx_tokens(text: str) -> int:
    """Cheap, provider-agnostic token estimate: ~4 chars/token. Good enough for budgets."""
    if not text:
        return 0
    return max(1, len(text) // 4)