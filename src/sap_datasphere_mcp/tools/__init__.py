# SAP Datasphere MCP Server
# File: tools/__init__.py
# Version: v1

"""Helpers for registering MCP tools."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP  # type: ignore[import]

from ..client import DatasphereClient
from . import spaces, catalog, data


def register_all_tools(mcp: FastMCP, client: DatasphereClient) -> None:
    """Register all MCP tools exposed by this server."""
    spaces.register_tools(mcp, client)
    catalog.register_tools(mcp, client)
    data.register_tools(mcp, client)
