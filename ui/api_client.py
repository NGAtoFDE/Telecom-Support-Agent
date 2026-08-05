"""Typed HTTP wrapper around the Telecom Support Agent API.

This is the ONLY place API URLs appear. The UI is a pure HTTP client (README §8): it must
never import from the ``telecom_agent`` package. All requests carry the ``X-API-Key`` header
and a client-generated ``X-Trace-Id`` so a turn can be correlated end to end.
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field
from typing import Any

import httpx


class ApiError(Exception):
    """Raised when the API returns the standard error envelope or an unexpected status."""

    def __init__(
        self, code: str, message: str, trace_id: str = "", retryable: bool = False
    ) -> None:
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message
        self.trace_id = trace_id
        self.retryable = retryable


@dataclass
class ApiClient:
    base_url: str = field(
        default_factory=lambda: os.getenv("API_BASE_URL", "http://localhost:8000")
    )
    api_key: str = field(default_factory=lambda: os.getenv("API_KEY", "dev-key-change-me"))
    timeout: float = 300.0

    def _headers(self, trace_id: str | None = None) -> dict[str, str]:
        headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}
        headers["X-Trace-Id"] = trace_id or uuid.uuid4().hex
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        params: dict | None = None,
        authed: bool = True,
    ) -> Any:
        url = f"{self.base_url.rstrip('/')}{path}"
        headers = self._headers() if authed else {}
        try:
            resp = httpx.request(
                method, url, json=json, params=params, headers=headers, timeout=self.timeout
            )
        except httpx.RequestError as exc:  # network / connection failure
            raise ApiError("CONNECTION_ERROR", f"could not reach API at {url}: {exc}") from exc

        # One error envelope everywhere: {"error": {code, message, trace_id, retryable}}
        if resp.status_code >= 400:
            body = _safe_json(resp)
            err = body.get("error") if isinstance(body, dict) else None
            if err:
                raise ApiError(
                    err.get("code", "ERROR"),
                    err.get("message", resp.text),
                    err.get("trace_id", ""),
                    err.get("retryable", False),
                )
            raise ApiError(f"HTTP_{resp.status_code}", resp.text)
        return _safe_json(resp)

    # -- endpoints ----------------------------------------------------------
    def chat(
        self, message: str, session_id: str | None = None, customer_ctx: dict | None = None
    ) -> dict:
        payload: dict = {"message": message}
        if session_id:
            payload["session_id"] = session_id
        if customer_ctx:
            payload["customer_ctx"] = customer_ctx
        return self._request("POST", "/v1/chat", json=payload)

    def classify(self, message: str, session_id: str | None = None) -> dict:
        payload: dict = {"message": message}
        if session_id:
            payload["session_id"] = session_id
        return self._request("POST", "/v1/classify", json=payload)

    def list_tickets(
        self,
        queue: str | None = None,
        priority: str | None = None,
        status: str | None = None,
        limit: int = 25,
    ) -> list[dict]:
        params = {
            k: v
            for k, v in {
                "queue": queue,
                "priority": priority,
                "status": status,
                "limit": limit,
            }.items()
            if v is not None
        }
        return self._request("GET", "/v1/tickets", params=params)

    def get_ticket(self, ticket_id: str) -> dict:
        return self._request("GET", f"/v1/tickets/{ticket_id}")

    def send_feedback(self, trace_id: str, session_id: str, thumbs: str, comment: str = "") -> dict:
        return self._request(
            "POST",
            "/v1/feedback",
            json={
                "trace_id": trace_id,
                "session_id": session_id,
                "thumbs": thumbs,
                "comment": comment,
            },
        )

    def readyz(self) -> dict:
        return self._request("GET", "/readyz", authed=False)

    def healthz(self) -> dict:
        return self._request("GET", "/healthz", authed=False)


def _safe_json(resp: httpx.Response) -> Any:
    try:
        return resp.json()
    except Exception:  # noqa: BLE001
        return {"raw": resp.text}
