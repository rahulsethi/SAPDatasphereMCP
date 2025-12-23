# SAP Datasphere MCP Server
# File: tests/test_plugin_registry.py
# Version: v1

from __future__ import annotations

import sys
import types

from sap_datasphere_mcp.plugins import registry


class DummyServer:
    """Minimal duck-typed MCP server for plugin registration tests."""

    def tool(self, *args, **kwargs):
        def decorator(fn):
            return fn

        return decorator


def test_register_plugins_no_env(monkeypatch):
    monkeypatch.delenv("DATASPHERE_PLUGINS", raising=False)
    out = registry.register_plugins(DummyServer())
    assert out["loaded"] == 0
    assert out["failed"] == 0
    assert out["plugins"] == []


def test_register_plugins_loads_module_from_sys_modules(monkeypatch):
    mod_name = "tests._dummy_plugin_mod"
    dummy = types.ModuleType(mod_name)

    called = {"ok": False}

    def register_tools(server):
        called["ok"] = True

        @server.tool(name="dummy_tool", description="dummy")
        async def _dummy_tool():
            return {"ok": True}

    dummy.register_tools = register_tools
    sys.modules[mod_name] = dummy

    monkeypatch.setenv("DATASPHERE_PLUGINS", mod_name)
    out = registry.register_plugins(DummyServer())

    assert called["ok"] is True
    assert out["loaded"] == 1
    assert out["failed"] == 0
    assert out["plugins"][0]["name"] == mod_name
    assert out["plugins"][0]["ok"] is True

    sys.modules.pop(mod_name, None)


def test_register_plugins_missing_module(monkeypatch):
    monkeypatch.setenv("DATASPHERE_PLUGINS", "this.module.does.not.exist_12345")
    out = registry.register_plugins(DummyServer())
    assert out["loaded"] == 0
    assert out["failed"] == 1
    assert out["plugins"][0]["ok"] is False
    assert out["plugins"][0]["error"]


def test_register_plugins_module_without_register_tools(monkeypatch):
    mod_name = "tests._dummy_plugin_no_register"
    dummy = types.ModuleType(mod_name)
    sys.modules[mod_name] = dummy

    monkeypatch.setenv("DATASPHERE_PLUGINS", mod_name)
    out = registry.register_plugins(DummyServer())

    assert out["loaded"] == 0
    assert out["failed"] == 1
    assert out["plugins"][0]["ok"] is False
    assert out["plugins"][0]["error"]

    sys.modules.pop(mod_name, None)
