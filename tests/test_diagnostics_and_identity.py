# SAP Datasphere MCP Server
# File: tests/test_diagnostics_and_identity.py
# Version: v1

import pytest

from sap_datasphere_mcp.tools import tasks


class _FakeHealthyClient:
    """Tiny fake client used to test diagnostics without real HTTP calls."""

    def __init__(self) -> None:
        self._spaces = [
            type("S", (), {"id": "SPACE_1", "name": "Demo Space", "description": "Demo"})()
        ]

    async def ping(self) -> bool:
        return True

    async def list_spaces(self):
        return self._spaces


@pytest.mark.asyncio
async def test_diagnostics_healthy(monkeypatch):
    """diagnostics should report ok=True when client and basic calls work."""

    monkeypatch.setattr(tasks, "_make_client", lambda: _FakeHealthyClient())

    result = await tasks.diagnostics()
    assert result["ok"] is True
    check_names = {c["name"] for c in result["checks"]}
    assert {"client_init", "ping", "list_spaces"} <= check_names


@pytest.mark.asyncio
async def test_tenant_info_uses_env(monkeypatch):
    """get_tenant_info should reflect env without leaking secrets."""

    monkeypatch.setenv("DATASPHERE_TENANT_URL", "https://my-tenant.eu10.hcs.cloud.sap")
    monkeypatch.setenv("DATASPHERE_OAUTH_TOKEN_URL", "https://my-uaa/oauth/token")
    monkeypatch.setenv("DATASPHERE_OAUTH_CLIENT_ID", "client-id")
    monkeypatch.setenv("DATASPHERE_OAUTH_CLIENT_SECRET", "super-secret")
    monkeypatch.setenv("DATASPHERE_VERIFY_TLS", "1")
    monkeypatch.setenv("DATASPHERE_MOCK_MODE", "0")

    info = await tasks.get_tenant_info()
    assert info["tenant_url"] == "https://my-tenant.eu10.hcs.cloud.sap"
    assert info["host"] == "my-tenant.eu10.hcs.cloud.sap"
    assert info["oauth"]["client_id_configured"] is True
    assert info["oauth"]["client_secret_configured"] is True
    assert info["mock_mode"] is False


@pytest.mark.asyncio
async def test_get_current_user_mock_mode(monkeypatch):
    """In mock mode we expose a friendly synthetic technical user."""

    monkeypatch.setenv("DATASPHERE_TENANT_URL", "https://mock-tenant.eu10.hcs.cloud.sap")
    monkeypatch.setenv("DATASPHERE_MOCK_MODE", "1")

    user_info = await tasks.get_current_user()
    assert user_info["mock_mode"] is True
    assert user_info["user"]["user_known"] is True
    assert user_info["user"]["source"] == "mock-mode"


@pytest.mark.asyncio
async def test_diagnostics_mock_mode(monkeypatch):
    """diagnostics should work end-to-end in DATASPHERE_MOCK_MODE."""

    # Minimal config needed for DatasphereConfig.from_env()
    monkeypatch.setenv("DATASPHERE_TENANT_URL", "https://mock-tenant.eu10.hcs.cloud.sap")
    monkeypatch.setenv(
        "DATASPHERE_OAUTH_TOKEN_URL",
        "https://mock-tenant.authentication.eu10.hana.ondemand.com/oauth/token",
    )
    monkeypatch.setenv("DATASPHERE_OAUTH_CLIENT_ID", "dummy-id")
    monkeypatch.setenv("DATASPHERE_OAUTH_CLIENT_SECRET", "dummy-secret")
    monkeypatch.setenv("DATASPHERE_VERIFY_TLS", "1")
    monkeypatch.setenv("DATASPHERE_MOCK_MODE", "1")

    result = await tasks.diagnostics()
    assert result["ok"] is True
    assert result["mock_mode"] is True
    names = {c["name"] for c in result["checks"]}
    assert "client_init" in names
    assert "ping" in names
    assert "list_spaces" in names
