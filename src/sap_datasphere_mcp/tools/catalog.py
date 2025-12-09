# SAP Datasphere MCP Server
# File: tools/catalog.py
# Version: v1

"""Catalog-related MCP tools.

Phase B will add tools like list_spaces, list_space_assets, etc.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP  # type: ignore[import]

from ..client import DatasphereClient


def register_tools(mcp: FastMCP, client: DatasphereClient) -> None:  # noqa: ARG001
    """Register catalog-related tools on the FastMCP instance.

    Placeholder for Phase B.
    """
    return None
