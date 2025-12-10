# SAP Datasphere MCP Server
# File: tools/tasks.py
# Version: v5

"""MCP-friendly async tasks backed by DatasphereClient.

These functions implement the core business logic and are designed to be
both:

- easy to call directly from smoke tests, and
- easy to expose as MCP tools from transports (stdio / http).

All public coroutines return only JSON-serialisable structures.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ..auth import OAuthClient
from ..client import DatasphereClient
from ..config import DatasphereConfig


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------


def _make_client() -> DatasphereClient:
    """Create a DatasphereClient from environment variables."""

    cfg = DatasphereConfig.from_env()
    oauth = OAuthClient(config=cfg)
    return DatasphereClient(config=cfg, oauth=oauth)


# ---------------------------------------------------------------------------
# Core async tasks (library-style)
# ---------------------------------------------------------------------------


async def ping() -> Dict[str, Any]:
    """Lightweight health check for the Datasphere configuration.

    Returns
    -------
    dict
        JSON-serialisable object with an ``ok`` flag.
    """
    client = _make_client()
    ok = await client.ping()
    return {"ok": bool(ok)}


async def list_spaces() -> Dict[str, Any]:
    """List SAP Datasphere spaces visible to this OAuth client.

    Returns
    -------
    dict
        {"spaces": [ {id, name, description}, ... ]}
    """
    client = _make_client()
    spaces = await client.list_spaces()

    items: List[Dict[str, Any]] = []
    for s in spaces:
        items.append(
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
            }
        )

    return {"spaces": items}


async def list_assets(space_id: str) -> Dict[str, Any]:
    """List catalog assets within a given space.

    Parameters
    ----------
    space_id:
        Technical ID / name of the Datasphere space.

    Returns
    -------
    dict
        {
          "space_id": "<space_id>",
          "assets": [
            {id, name, type, space_id, description},
            ...
          ]
        }
    """
    client = _make_client()
    assets = await client.list_space_assets(space_id=space_id)

    items: List[Dict[str, Any]] = []
    for a in assets:
        items.append(
            {
                "id": a.id,
                "name": a.name,
                "type": a.type,
                "space_id": a.space_id,
                "description": a.description,
            }
        )

    return {"space_id": space_id, "assets": items}


async def preview_asset(
    space_id: str,
    asset_name: str,
    top: int = 20,
) -> Dict[str, Any]:
    """Fetch a small sample of rows from a Datasphere asset.

    This is the same logic you already tested in ``test_mcp_preview_tool.py``,
    just factored into a reusable task.

    Parameters
    ----------
    space_id:
        Space that owns the asset.
    asset_name:
        Technical name / ID of the asset.
    top:
        Maximum number of rows to return.

    Returns
    -------
    dict
        {
          "columns":  [col_name, ...],
          "rows":     [[...], [...], ...],
          "truncated": bool,
          "meta":     {...}
        }
    """
    client = _make_client()
    result = await client.preview_asset_data(
        space_id=space_id,
        asset_name=asset_name,
        top=top,
    )

    return {
        "columns": result.columns,
        "rows": result.rows,
        "truncated": result.truncated,
        "meta": result.meta,
    }


# ---------------------------------------------------------------------------
# MCP tool registration
# ---------------------------------------------------------------------------


def register_tools(server: Any) -> None:
    """Register MCP tools on an ``mcp.server.Server`` instance.

    We deliberately keep this dependency-light: ``server`` is treated as a
    duck-typed object that just needs a ``.tool`` decorator.
    """

    if server is None or not hasattr(server, "tool"):
        raise ValueError(
            "register_tools(server) expects an MCP Server-like object "
            "that exposes a .tool() decorator."
        )

    # --- ping ----------------------------------------------------------------

    @server.tool(
        name="datasphere_ping",
        description="Basic health check for the SAP Datasphere MCP server.",
    )
    async def mcp_ping() -> Dict[str, Any]:
        return await ping()

    # --- list_spaces ---------------------------------------------------------

    @server.tool(
        name="datasphere_list_spaces",
        description="List SAP Datasphere spaces visible to this OAuth client.",
    )
    async def mcp_list_spaces() -> Dict[str, Any]:
        return await list_spaces()

    # --- list_assets ---------------------------------------------------------

    @server.tool(
        name="datasphere_list_assets",
        description="List catalog assets in a given SAP Datasphere space.",
    )
    async def mcp_list_assets(space_id: str) -> Dict[str, Any]:
        return await list_assets(space_id=space_id)

    # --- preview_asset -------------------------------------------------------

    @server.tool(
        name="datasphere_preview_asset",
        description="Preview a small set of rows from a Datasphere asset.",
    )
    async def mcp_preview_asset(
        space_id: str,
        asset_name: str,
        top: int = 20,
    ) -> Dict[str, Any]:
        return await preview_asset(
            space_id=space_id,
            asset_name=asset_name,
            top=top,
        )
