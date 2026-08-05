"""
Enterprise API Client

Single source of truth for all backend communication.

Responsibilities:
- Authentication
- Trace propagation
- Error normalization
- HTTP transport
- API endpoint access

UI must never import telecom_agent directly.
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field
from typing import Any

import httpx


# =========================================================
# ERRORS
# =========================================================


class ApiError(Exception):
    """Unified API exception."""

    def __init__(
        self,
        code: str,
        message: str,
        trace_id: str = "",
        retryable: bool = False,
    ) -> None:
        super().__init__(f"[{code}] {message}")

        self.code = code
        self.message = message
        self.trace_id = trace_id
        self.retryable = retryable


# =========================================================
# CLIENT
# =========================================================


@dataclass
class ApiClient:

    base_url: str = field(
        default_factory=lambda: os.getenv(
            "API_BASE_URL",
            "http://localhost:8000",
        )
    )

    api_key: str = field(
        default_factory=lambda: os.getenv(
            "API_KEY",
            "dev-key-change-me",
        )
    )

    timeout: float = 300.0

    def __post_init__(self) -> None:

        self.client = httpx.Client(
            timeout=self.timeout,
            follow_redirects=True,
        )

    # =====================================================
    # HELPERS
    # =====================================================

    def _generate_trace_id(self) -> str:
        return uuid.uuid4().hex

    def _headers(
        self,
        trace_id: str | None = None,
    ) -> dict[str, str]:

        return {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
            "X-Trace-Id": trace_id or self._generate_trace_id(),
        }

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        params: dict | None = None,
        authed: bool = True,
        trace_id: str | None = None,
    ) -> Any:

        url = f"{self.base_url.rstrip('/')}{path}"

        headers = (
            self._headers(trace_id)
            if authed
            else {}
        )

        try:

            response = self.client.request(
                method=method,
                url=url,
                json=json,
                params=params,
                headers=headers,
            )

        except httpx.TimeoutException as exc:

            raise ApiError(
                "TIMEOUT",
                f"Request timed out connecting to {url}",
                retryable=True,
            ) from exc

        except httpx.RequestError as exc:

            raise ApiError(
                "CONNECTION_ERROR",
                f"Unable to connect to API: {exc}",
                retryable=True,
            ) from exc

        if response.status_code >= 400:

            body = _safe_json(response)

            if (
                isinstance(body, dict)
                and "error" in body
            ):

                error = body["error"]

                raise ApiError(
                    error.get("code", "ERROR"),
                    error.get(
                        "message",
                        response.text,
                    ),
                    error.get(
                        "trace_id",
                        "",
                    ),
                    error.get(
                        "retryable",
                        False,
                    ),
                )

            raise ApiError(
                f"HTTP_{response.status_code}",
                response.text,
            )

        return _safe_json(response)

    # =====================================================
    # CHAT
    # =====================================================

    def chat(
        self,
        message: str,
        session_id: str | None = None,
        customer_ctx: dict | None = None,
    ) -> dict:

        payload: dict[str, Any] = {
            "message": message
        }

        if session_id:
            payload["session_id"] = session_id

        if customer_ctx:
            payload["customer_ctx"] = customer_ctx

        return self._request(
            "POST",
            "/v1/chat",
            json=payload,
        )

    # =====================================================
    # CLASSIFICATION
    # =====================================================

    def classify(
        self,
        message: str,
        session_id: str | None = None,
    ) -> dict:

        payload: dict[str, Any] = {
            "message": message
        }

        if session_id:
            payload["session_id"] = session_id

        return self._request(
            "POST",
            "/v1/classify",
            json=payload,
        )

    # =====================================================
    # TICKETS
    # =====================================================

    def list_tickets(self, queue: str | None = None, priority: str | None = None, status: str | None = None, limit: int = 25,) -> list[dict]:
        params={k: v for k, v in {"queue": queue, "priority": priority, "status": status, "limit": limit,}.items()
            if v is not None
        }

        return self._request(
            "GET",
            "/v1/tickets",
            params=params,
        )

    def get_ticket(
        self,
        ticket_id: str,
    ) -> dict:

        return self._request(
            "GET",
            f"/v1/tickets/{ticket_id}",
        )

    # =====================================================
    # FEEDBACK
    # =====================================================

    def send_feedback(
        self,
        trace_id: str,
        session_id: str,
        thumbs: str,
        comment: str = "",
    ) -> dict:

        return self._request(
            "POST",
            "/v1/feedback",
            json={
                "trace_id": trace_id,
                "session_id": session_id,
                "thumbs": thumbs,
                "comment": comment,
            },
            trace_id=trace_id,
        )

    # =====================================================
    # HEALTH
    # =====================================================

    def readyz(self) -> dict:
        return self._request(
            "GET",
            "/readyz",
            authed=False,
        )

    def healthz(self) -> dict:
        return self._request(
            "GET",
            "/healthz",
            authed=False,
        )

    # =====================================================
    # CLEANUP
    # =====================================================

    def close(self) -> None:

        try:
            self.client.close()
        except Exception:
            pass


# =========================================================
# JSON SAFETY
# =========================================================


def _safe_json(
    response: httpx.Response,
) -> Any:

    try:
        return response.json()

    except Exception:
        return {
            "raw": response.text
        }