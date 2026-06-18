# SAP Datasphere MCP Server
# File: tests/test_v1_registry.py
# Version: v1 (1.0)

"""End-to-end tests for the v1.0 tool registry, governance tools, and prompts/resources wiring."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Tuple

import pytest

from sap_datasphere_mcp import policy, redaction
from sap_datasphere_mcp.tools import _aliases, _metadata
from sap_datasphere_mcp.tools.governance import api_policy_check, audit_tail


class FakeMCPServer:
    """Captures every `.tool()` / `.prompt()` / `.resource()` registration."""

    def __init__(self) -> None:
        self.tools: List[Tuple[str, Dict[str, Any]]] = []
        self.prompts: List[Tuple[str, Dict[str, Any]]] = []
        self.resources: List[Tuple[str, Dict[str, Any]]] = []

    def tool(self, name: str, description: str = "", annotations: Any = None):
        def _decorator(fn):
            self.tools.append((name, {"description": description, "annotations": annotations, "fn": fn}))
            return fn
        return _decorator

    def prompt(self, name: str, description: str = ""):
        def _decorator(fn):
            self.prompts.append((name, {"description": description, "fn": fn}))
            return fn
        return _decorator

    def resource(self, uri: str, name: str = "", description: str = "", mime_type: str = ""):
        def _decorator(fn):
            self.resources.append((uri, {"name": name, "description": description, "mime_type": mime_type, "fn": fn}))
            return fn
        return _decorator


def test_metadata_registry_counts():
    """All 24 v1.0 tools present, all read-only, none destructive."""
    assert len(_metadata.TOOL_REGISTRY) == 24
    for name, meta in _metadata.TOOL_REGISTRY.items():
        assert meta.read_only is True, f"{name} is not read_only"
        assert meta.destructive is False, f"{name} is destructive"
        assert meta.policy_class in {"permitted_always", "permitted_under_cc", "gated"}


def test_legacy_aliases_built_from_metadata():
    """Every legacy_name in metadata appears in LEGACY_ALIASES with the right target."""
    expected = {
        "datasphere_ping": "datasphere_connectivity_ping",
        "datasphere_diagnostics": "datasphere_connectivity_diagnostics",
        "datasphere_get_tenant_info": "datasphere_connectivity_tenant_info",
        "datasphere_get_current_user": "datasphere_connectivity_whoami",
        "datasphere_plugins_status": "datasphere_connectivity_plugins_status",
        "datasphere_list_spaces": "datasphere_catalog_list_spaces",
        "datasphere_list_assets": "datasphere_catalog_list_assets",
        "datasphere_get_asset_metadata": "datasphere_catalog_get_asset",
        "datasphere_list_columns": "datasphere_catalog_list_columns",
        "datasphere_space_summary": "datasphere_catalog_space_overview",
        "datasphere_preview_asset": "datasphere_query_preview",
        "datasphere_search_assets": "datasphere_discover_assets",
        "datasphere_find_assets_with_column": "datasphere_discover_assets_with_column",
        "datasphere_find_assets_by_column": "datasphere_discover_assets_by_column",
        "datasphere_describe_asset_schema": "datasphere_profile_schema",
        "datasphere_compare_assets_basic": "datasphere_summarize_compare_assets",
    }
    assert _aliases.LEGACY_ALIASES == expected


def test_registry_registers_canonical_and_aliases():
    """register_all() wires both new names and every legacy alias."""
    from sap_datasphere_mcp.tools.registry import register_all

    fake = FakeMCPServer()
    register_all(fake)

    registered_names = {name for name, _ in fake.tools}
    # 24 canonical names
    for canonical_name in _metadata.TOOL_REGISTRY:
        assert canonical_name in registered_names, f"missing canonical: {canonical_name}"
    # 16 legacy aliases
    for legacy_name in _aliases.LEGACY_ALIASES:
        assert legacy_name in registered_names, f"missing alias: {legacy_name}"
    assert len(fake.tools) == 24 + 16


def test_prompts_register_five():
    from sap_datasphere_mcp.prompts import register

    fake = FakeMCPServer()
    register(fake)
    prompt_names = [name for name, _ in fake.prompts]
    assert sorted(prompt_names) == sorted(
        [
            "profile_dataset",
            "audit_space",
            "explain_analytical_model",
            "compare_assets",
            "find_data_about_topic",
        ]
    )


def test_resources_register_four():
    from sap_datasphere_mcp.resources import register

    fake = FakeMCPServer()
    register(fake)
    uris = [uri for uri, _ in fake.resources]
    assert uris == [
        "datasphere://space/{space_id}",
        "datasphere://space/{space_id}/asset/{asset_name}",
        "datasphere://space/{space_id}/asset/{asset_name}/schema",
        "datasphere://space/{space_id}/asset/{asset_name}/sample",
    ]


def test_create_server_smoke():
    """End-to-end: server.create_server() returns a FastMCP without raising."""
    from sap_datasphere_mcp.server import create_server

    mcp = create_server()
    assert mcp is not None
    assert hasattr(mcp, "tool")


@pytest.mark.asyncio
async def test_governance_api_policy_check_shape():
    result = await api_policy_check()
    assert result["ok"] is True
    assert result["policy_version"] == "v4.2026a"
    assert "deployment_posture" in result
    assert "tools_by_class" in result
    classes = result["tools_by_class"]
    assert "permitted_always" in classes
    assert "permitted_under_cc" in classes
    assert "gated" in classes
    # No tool is policy-gated at 1.0.
    assert classes["gated"] == []
    # Connectivity + governance live in permitted_always.
    assert "datasphere_connectivity_ping" in classes["permitted_always"]
    assert "datasphere_governance_api_policy_check" in classes["permitted_always"]


@pytest.mark.asyncio
async def test_governance_audit_tail_disabled_by_default(monkeypatch, tmp_path):
    monkeypatch.delenv("DATASPHERE_AUDIT_ENABLED", raising=False)
    # Force a fresh log instance pointed at a tmp file so we don't depend on global state.
    from sap_datasphere_mcp import audit as audit_mod
    audit_mod.reset_audit_log_for_tests()
    monkeypatch.setenv("DATASPHERE_AUDIT_LOG_PATH", str(tmp_path / "audit.log"))

    result = await audit_tail(limit=10)
    assert result["ok"] is True
    assert result["records"] == []
    assert result["meta"]["audit_enabled"] is False


def test_redaction_scrubs_secret_in_secret_field():
    raw = {
        "user": "alice",
        "client_secret": "abcdefghijklmnopqrstuvwxyz0123456789ABCDEF==",
        "rows": [{"id": 1, "note": "this is just data"}],
    }
    cleaned = redaction._walk(raw)
    assert cleaned["client_secret"] == "<redacted>"
    assert cleaned["user"] == "alice"
    assert cleaned["rows"][0]["note"] == "this is just data"


def test_redaction_scrubs_jwt_anywhere():
    raw = {"trace": "Authorization: Bearer eyJhbGc.eyJzdWI.signaturepart_more123"}
    cleaned = redaction._walk(raw)
    assert "eyJ" not in cleaned["trace"]


def test_policy_gate_strict_refuses_gated_tool():
    # No tool is gated at 1.0, but the gate logic itself must work.
    decision = policy.permits("hypothetical", policy_class="gated", strict=True)
    assert decision.allowed is False
    assert decision.policy_class == "gated"


def test_policy_gate_strict_allows_permitted_tools():
    decision = policy.permits("datasphere_catalog_list_spaces", policy_class="permitted_under_cc", strict=True)
    assert decision.allowed is True


def test_alias_logs_deprecation_warning_once(caplog):
    """An alias call logs a single deprecation warning the first time it's used."""
    from sap_datasphere_mcp.tools import _gated, _metadata

    meta = _metadata.TOOL_REGISTRY["datasphere_connectivity_ping"]

    async def fake_impl():
        return {"ok": True}

    wrapped = _gated.wrap_tool(meta, fake_impl)
    alias = _gated.make_alias("datasphere_ping", meta, wrapped)

    caplog.set_level("WARNING", logger="sap_datasphere_mcp.tools")

    async def call_twice():
        await alias()
        await alias()

    asyncio.run(call_twice())
    deprecation_records = [r for r in caplog.records if "tool_alias_used" in r.getMessage()]
    assert len(deprecation_records) == 1
