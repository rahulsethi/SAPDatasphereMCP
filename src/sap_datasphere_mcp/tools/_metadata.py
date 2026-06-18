# SAP Datasphere MCP Server
# File: tools/_metadata.py
# Version: v1 (1.0)

"""Centralized per-tool risk and policy metadata.

Drives:
- MCP tool annotations (readOnlyHint, idempotentHint, destructiveHint)
- API Policy v4/2026 gate (see :mod:`sap_datasphere_mcp.policy`)
- Audit log enrichment
- README per-tool risk table generation
- Legacy alias mapping
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterator, List, Optional, Tuple

__all__ = ["ToolMetadata", "TOOL_REGISTRY", "iter_tools", "by_legacy_name"]


@dataclass(frozen=True)
class ToolMetadata:
    """Per-tool risk + policy descriptor.

    See :mod:`sap_datasphere_mcp.policy_evidence` for the meaning of
    ``policy_class``. ``risk_level`` is informational; nothing currently
    gates on it.
    """

    name: str
    category: str
    description: str
    legacy_name: Optional[str] = None
    risk_level: str = "low"
    data_class: str = "metadata"  # none | metadata | sample-data | full-data
    policy_class: str = "permitted_under_cc"  # permitted_always | permitted_under_cc | gated
    read_only: bool = True
    idempotent: bool = False
    destructive: bool = False
    open_world: bool = True


# --- Canonical tool registry (single source of truth) -----------------------

_TOOLS: List[ToolMetadata] = [
    # === connectivity (5) ===
    ToolMetadata(
        name="datasphere_connectivity_ping",
        legacy_name="datasphere_ping",
        category="connectivity",
        description="Basic health check for the SAP Datasphere MCP server.",
        data_class="none",
        policy_class="permitted_always",
        idempotent=True,
    ),
    ToolMetadata(
        name="datasphere_connectivity_diagnostics",
        legacy_name="datasphere_diagnostics",
        category="connectivity",
        description="High-level diagnostics covering client init, ping, list_spaces, mock/live mode, and elapsed time.",
        data_class="none",
        policy_class="permitted_always",
    ),
    ToolMetadata(
        name="datasphere_connectivity_tenant_info",
        legacy_name="datasphere_get_tenant_info",
        category="connectivity",
        description="Redacted snapshot of tenant configuration (URLs, region hint, TLS settings, OAuth presence).",
        data_class="none",
        policy_class="permitted_always",
        idempotent=True,
    ),
    ToolMetadata(
        name="datasphere_connectivity_whoami",
        legacy_name="datasphere_get_current_user",
        category="connectivity",
        description="Describes the current Datasphere identity context (technical user vs mock mode).",
        data_class="none",
        policy_class="permitted_always",
        idempotent=True,
    ),
    ToolMetadata(
        name="datasphere_connectivity_plugins_status",
        legacy_name="datasphere_plugins_status",
        category="connectivity",
        description="Status of registered plugin modules (loaded / missing / error).",
        data_class="none",
        policy_class="permitted_always",
    ),
    # === catalog (5) ===
    ToolMetadata(
        name="datasphere_catalog_list_spaces",
        legacy_name="datasphere_list_spaces",
        category="catalog",
        description="List SAP Datasphere spaces visible to this OAuth client.",
        idempotent=True,
    ),
    ToolMetadata(
        name="datasphere_catalog_list_assets",
        legacy_name="datasphere_list_assets",
        category="catalog",
        description="List catalog assets (tables/views/models) in a given Datasphere space.",
        idempotent=True,
    ),
    ToolMetadata(
        name="datasphere_catalog_get_asset",
        legacy_name="datasphere_get_asset_metadata",
        category="catalog",
        description="Fetch catalog metadata for a single asset: ids, labels, descriptions, exposure flags, raw payload.",
        idempotent=True,
    ),
    ToolMetadata(
        name="datasphere_catalog_list_columns",
        legacy_name="datasphere_list_columns",
        category="catalog",
        description="List columns via relational $metadata (EDMX/XML) when available, falling back to preview-based inference.",
        idempotent=True,
    ),
    ToolMetadata(
        name="datasphere_catalog_space_overview",
        legacy_name="datasphere_space_summary",
        category="catalog",
        description="Quick overview of a space: total assets, counts by type, and a sample list of assets.",
        idempotent=True,
    ),
    # === query (3) ===
    ToolMetadata(
        name="datasphere_query_preview",
        legacy_name="datasphere_preview_asset",
        category="query",
        description="Preview a small set of rows from a Datasphere asset.",
        data_class="sample-data",
    ),
    ToolMetadata(
        name="datasphere_query_relational",
        legacy_name=None,  # name unchanged
        category="query",
        description="Run an OData-style relational query with $select, $filter, $orderby, $top, $skip.",
        data_class="full-data",
    ),
    ToolMetadata(
        name="datasphere_query_analytical",
        legacy_name=None,
        category="query",
        description="Run an OData-style analytical query against an asset exposed via the analytical consumption API.",
        data_class="full-data",
    ),
    # === discover (3) ===
    ToolMetadata(
        name="datasphere_discover_assets",
        legacy_name="datasphere_search_assets",
        category="discover",
        description="Substring search on asset id, name, description, or type across one or many spaces.",
    ),
    ToolMetadata(
        name="datasphere_discover_assets_with_column",
        legacy_name="datasphere_find_assets_with_column",
        category="discover",
        description="Within a single space, scan up to max_assets to find assets exposing a given column name.",
    ),
    ToolMetadata(
        name="datasphere_discover_assets_by_column",
        legacy_name="datasphere_find_assets_by_column",
        category="discover",
        description="Search multiple spaces for assets exposing a given column, with caps on spaces/assets/results.",
    ),
    # === profile (2) ===
    ToolMetadata(
        name="datasphere_profile_schema",
        legacy_name="datasphere_describe_asset_schema",
        category="profile",
        description="Sample-based column summary: names, example values, rough type inference, null counts.",
        data_class="sample-data",
    ),
    ToolMetadata(
        name="datasphere_profile_column",
        legacy_name=None,
        category="profile",
        description="Statistical profile of a single column: counts, distincts, numeric stats, categorical summary, role hint.",
        data_class="sample-data",
    ),
    # === summarize (4) ===
    ToolMetadata(
        name="datasphere_summarize_asset",
        legacy_name=None,
        category="summarize",
        description="Deterministic LLM-friendly summary of an asset: schema + key columns + small profile.",
    ),
    ToolMetadata(
        name="datasphere_summarize_space",
        legacy_name=None,
        category="summarize",
        description="Deterministic LLM-friendly summary of a space: composition, key assets, overall shape.",
    ),
    ToolMetadata(
        name="datasphere_summarize_column_profile",
        legacy_name=None,
        category="summarize",
        description="Deterministic LLM-friendly summary derived from a column profile result.",
    ),
    ToolMetadata(
        name="datasphere_summarize_compare_assets",
        legacy_name="datasphere_compare_assets_basic",
        category="summarize",
        description="Structural comparison between two assets: column overlap, type mismatches, naming differences.",
    ),
    # === governance (2 NEW) ===
    ToolMetadata(
        name="datasphere_governance_api_policy_check",
        legacy_name=None,
        category="governance",
        description="Returns the SAP API Policy v4/2026 posture of this deployment: tier, audit state, policy classes, evidence.",
        data_class="none",
        policy_class="permitted_always",
        idempotent=True,
    ),
    ToolMetadata(
        name="datasphere_governance_audit_tail",
        legacy_name=None,
        category="governance",
        description="Return the last N records from the audit log (requires DATASPHERE_AUDIT_ENABLED=1).",
        data_class="metadata",
        policy_class="permitted_always",
    ),
]

#: Lookup by canonical (v1.0) name.
TOOL_REGISTRY: Dict[str, ToolMetadata] = {meta.name: meta for meta in _TOOLS}

#: Lookup by legacy (v0.3.x) name.
_BY_LEGACY: Dict[str, ToolMetadata] = {
    meta.legacy_name: meta for meta in _TOOLS if meta.legacy_name is not None
}


def iter_tools() -> Iterator[Tuple[str, ToolMetadata]]:
    """Iterate over (canonical_name, metadata) in registration order."""
    for meta in _TOOLS:
        yield meta.name, meta


def by_legacy_name(legacy_name: str) -> Optional[ToolMetadata]:
    """Return the v1.0 metadata for a v0.3.x tool name (or None)."""
    return _BY_LEGACY.get(legacy_name)
