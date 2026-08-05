"""Shared test fixtures. Everything runs offline against the fake provider.

Test environment is set at import time (before any ``telecom_agent`` module reads it) and
points at a throwaway temp dir holding a tiny self-contained KB, so the suite does not
depend on the repo's ``data/`` directory.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

# --- configure environment BEFORE importing the package -----------------------
_TMP = Path(tempfile.mkdtemp(prefix="teleco_test_"))
_KB = _TMP / "kb"
_KB.mkdir(parents=True, exist_ok=True)
_INDEX = _TMP / "index"


def _write_kb() -> None:
    docs = {
        "data_slow.md": (
            "doc_id: KB-001\n# Slow data troubleshooting\n"
            "## Steps\n"
            "If your mobile internet is slow or buffering, reset the network mode, clear the "
            "APN cache and toggle airplane mode. Slow data speed on 4G is often an APN or "
            "network congestion issue. Restart the phone and retry the internet connection.\n"
        ),
        "apn_reset.md": (
            "doc_id: KB-101\n# APN reset guide (Android)\n"
            "## Steps\n"
            "Open Settings, mobile network, Access Point Names. Reset the APN to default "
            "'internet'. Enable mobile data and hotspot. Reboot the device to restore data.\n"
        ),
        "no_service.md": (
            "doc_id: KB-201\n# No service / no signal\n"
            "## Steps\n"
            "If there is no service or no signal, check for a network outage in your circle, "
            "restart the phone, reseat the SIM, and select the network operator manually. "
            "A suspected tower outage is escalated to the network operations centre.\n"
        ),
        "recharge_failed.md": (
            "doc_id: KB-301\n# Recharge payment failed\n"
            "## Policy\n"
            "If a recharge payment failed but money was deducted, the transaction is auto "
            "reversed within 5 working days. Share the transaction reference for a refund. "
            "Error ERR-RCH-402 indicates a gateway timeout on the recharge.\n"
        ),
    }
    for name, body in docs.items():
        (_KB / name).write_text(body, encoding="utf-8")


_write_kb()

_DB_URL = "sqlite:///" + str(_TMP / "app.db").replace("\\", "/")
os.environ.update(
    {
        "LLM_PROVIDER": "fake",
        "API_KEY": "test-key",
        "APP_ENV": "local",
        "DATABASE_URL": _DB_URL,
        "KB_DIR": str(_KB),
        "INDEX_DIR": str(_INDEX),
        "AUTO_INGEST": "true",
        "LOG_LEVEL": "WARNING",
    }
)

# --- now safe to import the package -------------------------------------------
import pytest  # noqa: E402

from telecom_agent.api.deps import build_container  # noqa: E402
from telecom_agent.api.main import create_app  # noqa: E402
from telecom_agent.config.settings import get_settings  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield


@pytest.fixture(scope="session")
def settings():
    return get_settings()


@pytest.fixture(scope="session")
def api_key(settings):
    return settings.api_key


@pytest.fixture(scope="session")
def container(settings):
    return build_container(settings)


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app, api_key):
    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        c.headers.update({"X-API-Key": api_key})
        yield c
