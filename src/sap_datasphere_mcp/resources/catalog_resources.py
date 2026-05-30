# SAP Datasphere MCP Server
# File: resources/catalog_resources.py
# Version: v1 (1.0)

"""URI-pattern → resolver bindings for the catalog resources.

These mirror four of our most-useful catalog tool calls but expose them as
URI-addressable MCP resources. The implementation delegates to the existing
async functions in :mod:`sap_datasphere_mcp.tools.tasks` so behavior stays
consistent with the tool surface.
"""

from __future__ import annotations

import json
import os
from typing import Any

from ..tools import tasks

__all__ = ["register"]


def _sample_row_cap() -> int:
    raw = os.environ.get("DATASPHERE_RESOURCE_SAMPLE_ROWS", "5")
    try:
        return max(1, min(int(raw), 50))
    except ValueError:
        return 5


async def _space_resource(space_id: str) -> str:
    payload = await tasks.space_summary(space_id=space_id)
    return json.dumps(payload, indent=2, default=str)


async def _asset_resource(space_id: str, asset_name: str) -> str:
    payload = await tasks.get_asset_metadata(space_id=space_id, asset_name=asset_name)
    return json.dumps(payload, indent=2, default=str)


async def _asset_schema_resource(space_id: str, asset_name: str) -> str:
    payload = await tasks.list_columns(space_id=space_id, asset_name=asset_name)
    return json.dumps(payload, indent=2, default=str)


async def _asset_sample_resource(space_id: str, asset_name: str) -> str:
    payload = await tasks.preview_asset(
        space_id=space_id,
        asset_name=asset_name,
        top=_sample_row_cap(),
    )
    return json.dumps(payload, indent=2, default=str)


_BINDINGS = [
    (
        "datasphere://space/{space_id}",
        "Datasphere space metadata",
        "Quick overview for a given space: counts by type and a sample asset list.",
        _space_resource,
    ),
    (
        "datasphere://space/{space_id}/asset/{asset_name}",
        "Datasphere asset metadata",
        "Catalog metadata for a single asset (labels, description, exposure flags, raw payload).",
        _asset_resource,
    ),
    (
        "datasphere://space/{space_id}/asset/{asset_name}/schema",
        "Datasphere asset schema",
        "Column list for a single asset, via $metadata (EDMX) when available, sample-based fallback otherwise.",
        _asset_schema_resource,
    ),
    (
        "datasphere://space/{space_id}/asset/{asset_name}/sample",
        "Datasphere asset sample rows",
        "Capped sample of rows for a single asset (DATASPHERE_RESOURCE_SAMPLE_ROWS, default 5).",
        _asset_sample_resource,
    ),
]


def register(server: Any) -> None:
    """Register the four catalog-resource URI patterns."""
    for uri, name, description, fn in _BINDINGS:
        try:
            decorator = server.resource(uri, name=name, description=description, mime_type="application/json")
        except TypeError:
            try:
                decorator = server.resource(uri, name=name, description=description)
            except TypeError:
                decorator = server.resource(uri)
        decorator(fn)
