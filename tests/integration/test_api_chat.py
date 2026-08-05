"""API contract: /v1/chat shape, auth envelope, health, feedback."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def test_chat_returns_contract_shape(client):
    r = client.post("/v1/chat", json={"message": "my internet is slow"})
    assert r.status_code == 200, r.text
    body = r.json()
    for key in ("trace_id", "session_id", "resolution", "answer", "citations", "llm", "usage"):
        assert key in body
    assert body["llm"]["provider"] in {"FAKE", "AZURE_FOUNDRY", "GROQ"}
    assert isinstance(body["citations"], list)


def test_missing_api_key_returns_401_envelope(app):
    with TestClient(app) as c:  # no X-API-Key header
        r = c.post("/v1/chat", json={"message": "hi"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHORIZED"


def test_healthz(client):
    assert client.get("/healthz").json()["status"] == "ok"


def test_feedback_accepted(client):
    chat = client.post("/v1/chat", json={"message": "my internet is slow"}).json()
    r = client.post(
        "/v1/feedback",
        json={
            "trace_id": chat["trace_id"],
            "session_id": chat["session_id"],
            "thumbs": "up",
            "comment": "helpful",
        },
    )
    assert r.status_code == 200
    assert r.json()["accepted"] is True


def test_classify_endpoint(client):
    r = client.post("/v1/classify", json={"message": "I was overcharged on my bill, want a refund"})
    assert r.status_code == 200
    assert r.json()["category"] == "BILLING_DISPUTE"
