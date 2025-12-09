# SAP Datasphere MCP Server
# File: tools/spaces.py
# Version: v1

"""Space-related MCP tools."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP  # type: ignore[import]

from ..client import DatasphereClient


def register_tools(mcp: FastMCP, client: DatasphereClient) -> None:
    """Register space-related tools on the given FastMCP instance."""

    @mcp.tool()
    async def get_connection_status() -> dict:
        """Return basic health information for the Datasphere connection.

        Phase A: this only checks whether a tenant URL is configured.
        """
        healthy = await client.ping()
        status = "ok" if healthy else "not_configured"

        return {
            "summary": f"Datasphere client health: {status}",
            "data": {
                "healthy": healthy,
                "tenant_url_configured": bool(client.config.tenant_url),
            },
            "meta": {},
        }
