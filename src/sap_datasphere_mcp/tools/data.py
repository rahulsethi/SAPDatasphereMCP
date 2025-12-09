# SAP Datasphere MCP Server
# File: tools/data.py
# Version: v1

"""Data access MCP tools (preview & queries).

Phase C will add tools for previewing and querying data.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP  # type: ignore[import]

from ..client import DatasphereClient


def register_tools(mcp: FastMCP, client: DatasphereClient) -> None:  # noqa: ARG001
    """Register data-related tools on the FastMCP instance.

    Placeholder for Phase C.
    """
    return None
