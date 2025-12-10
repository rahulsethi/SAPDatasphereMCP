# SAP Datasphere MCP Server
# File: tools/catalog.py
# Version: v2

"""Catalog-related MCP tools (assets, metadata, etc.)."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP  # type: ignore[import]

from ..client import DatasphereClient


def register_tools(mcp: FastMCP, client: DatasphereClient) -> None:
    """Register catalog-related tools on the given FastMCP instance."""

    @mcp.tool()
    async def list_space_assets(space_id: str) -> dict:
        """List catalog assets in a given Datasphere space.

        Args:
            space_id:
                The technical ID or name of the space. This should match the
                `id` field returned by the `list_spaces` tool.

        Returns:
            A structured list of assets, including id, name and type.
        """
        assets = await client.list_space_assets(space_id=space_id)

        items = [
            {
                "id": a.id,
                "name": a.name,
                "type": a.type,
                "description": a.description,
            }
            for a in assets
        ]

        return {
            "summary": (
                f"Found {len(items)} catalog assets in space '{space_id}'."
            ),
            "data": items,
            "meta": {
                "space_id": space_id,
                "count": len(items),
            },
        }
