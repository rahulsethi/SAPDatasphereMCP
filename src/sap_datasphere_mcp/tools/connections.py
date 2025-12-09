# SAP Datasphere MCP Server
# File: tools/connections.py
# Version: v1

"""Connection-related MCP tools (future optional features)."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP  # type: ignore[import]

from ..client import DatasphereClient


def register_tools(mcp: FastMCP, client: DatasphereClient) -> None:  # noqa: ARG001
    """Placeholder for future connection-related tools."""
    return None
