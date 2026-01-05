# SAP Datasphere MCP Server
# File: tests/test_limits_cache_diagnostics.py
# Version: v1

from __future__ import annotations

import sys
import types

import pytest

from sap_datasphere_mcp.plugins import registry as plugin_registry
from sap_datasphere_mcp.tools import tasks


class DummyServer:
    def tool(self, *args, **kwargs):
        def decorator(fn):
            return fn

        return decorator


@pytest.mark.asyncio
async def test_preview_respects_env_row_cap(monkeypatch):
    monkeypatch.setenv("DATASPHERE_MOCK_MODE", "1")
    monkeypatch.setenv("DATASPHERE_MAX_ROWS_PREVIEW", "2")
    monkeypatch.setenv("DATASPHERE_CACHE_TTL_SECONDS", "0")
    monkeypatch.setenv("DATASPHERE_CACHE_MAX_ENTRIES", "0")

    out = await tasks.preview_asset(
        space_id="MOCK_SALES",
        asset_name="SALES_ORDERS",
        top=999,
    )

    assert len(out["rows"]) == 2
    assert out["meta"]["top"] == 2
    assert out["meta"]["requested_top"] == 999
    assert out["meta"]["effective_top"] == 2
    assert out["meta"]["cap_top"] == 2
    assert out["meta"]["cap_applied"] is True


@pytest.mark.asyncio
async def test_query_respects_env_row_cap(monkeypatch):
    monkeypatch.setenv("DATASPHERE_MOCK_MODE", "1")
    monkeypatch.setenv("DATASPHERE_MAX_ROWS_QUERY", "3")
    monkeypatch.setenv("DATASPHERE_CACHE_TTL_SECONDS", "0")
    monkeypatch.setenv("DATASPHERE_CACHE_MAX_ENTRIES", "0")

    out = await tasks.query_relational(
        space_id="MOCK_SALES",
        asset_name="SALES_ORDERS",
        top=999,
        skip=0,
    )

    assert len(out["rows"]) == 3
    assert out["meta"]["top"] == 3
    assert out["meta"]["requested_top"] == 999
    assert out["meta"]["effective_top"] == 3
    assert out["meta"]["cap_top"] == 3
    assert out["meta"]["cap_applied"] is True


@pytest.mark.asyncio
async def test_metadata_cache_hits_visible_in_diagnostics(monkeypatch):
    monkeypatch.setenv("DATASPHERE_MOCK_MODE", "1")
    monkeypatch.setenv("DATASPHERE_CACHE_TTL_SECONDS", "60")
    monkeypatch.setenv("DATASPHERE_CACHE_MAX_ENTRIES", "32")

    await tasks.list_spaces()
    await tasks.list_spaces()

    diag = await tasks.diagnostics()
    cache_stats = diag["meta"]["cache"]

    assert cache_stats["enabled"] is True
    assert cache_stats["hits"] >= 1
    assert cache_stats["size"] >= 1


@pytest.mark.asyncio
async def test_diagnostics_includes_plugin_status(monkeypatch):
    monkeypatch.setenv("DATASPHERE_MOCK_MODE", "1")
    monkeypatch.setenv("DATASPHERE_CACHE_TTL_SECONDS", "0")
    monkeypatch.setenv("DATASPHERE_CACHE_MAX_ENTRIES", "0")

    mod_name = "tests._dummy_plugin_for_diag"
    dummy = types.ModuleType(mod_name)

    def register_tools(server):
        @server.tool(name="dummy_tool", description="dummy")
        async def _dummy_tool():
            return {"ok": True}

    dummy.register_tools = register_tools
    sys.modules[mod_name] = dummy

    monkeypatch.setenv("DATASPHERE_PLUGINS", mod_name)
    plugin_registry.register_plugins(DummyServer())

    diag = await tasks.diagnostics()
    plugins = diag["meta"]["plugins"]

    assert plugins["configured"] == [mod_name]
    assert plugins["loaded"] == 1
    assert plugins["failed"] == 0
    assert plugins["plugins"][0]["name"] == mod_name
    assert plugins["plugins"][0]["ok"] is True

    sys.modules.pop(mod_name, None)
