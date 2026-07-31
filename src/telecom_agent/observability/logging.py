"""JSON structured logging with a redaction filter.

Every line carries whatever context is bound (trace_id, session_id, provider, node,
decision, scores). A redaction filter strips anything resembling a phone number, ICCID or
email *before* it leaves the process — synthetic data is treated as if it were real, which
is the habit that transfers to a client engagement (README §15).
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

_PHONE = re.compile(r"\b(?:\+?91[- ]?)?[6-9]\d{9}\b")
_ICCID = re.compile(r"\b\d{18,22}\b")
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_AADHAAR = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")


def redact(text: str) -> str:
    text = _EMAIL.sub("[email]", text)
    text = _AADHAAR.sub("[id]", text)
    text = _PHONE.sub("[phone]", text)
    text = _ICCID.sub("[iccid]", text)
    return text


class RedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact(record.msg)
        return True


class JsonFormatter(logging.Formatter):
    _RESERVED = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {"message", "asctime"}

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": redact(record.getMessage()),
        }
        for key, value in record.__dict__.items():
            if key not in self._RESERVED and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(level: str = "INFO", *, json_logs: bool = True) -> None:
    root = logging.getLogger()
    root.setLevel(level.upper())
    for h in list(root.handlers):
        root.removeHandler(h)
    handler = logging.StreamHandler()
    handler.addFilter(RedactionFilter())
    handler.setFormatter(
        JsonFormatter()
        if json_logs
        else logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )
    root.addHandler(handler)


def get_logger(name: str) -> logging.LoggerAdapter:
    return logging.LoggerAdapter(logging.getLogger(name), extra={})


def bind(logger_name: str, **context: Any) -> logging.LoggerAdapter:
    """Return a logger adapter that stamps ``context`` (trace_id, provider, ...) on every line."""
    return logging.LoggerAdapter(logging.getLogger(logger_name), extra=context)
