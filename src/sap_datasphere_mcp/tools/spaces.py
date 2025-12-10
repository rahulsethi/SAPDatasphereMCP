# SAP Datasphere MCP Server
# File: tools/spaces.py
# Version: v2

"""Space-related MCP tools."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP  # type: ignore[import]

from ..client import DatasphereClient


def register_tools(mcp: FastMCP, client: DatasphereClient) -> None:
    """Register space-related tools on the given FastMCP instance."""

    @mcp.tool()
    async def get_connection_status() -> dict:
        """Return basic health information for the Datasphere connection.

        Currently this checks whether the tenant URL is configured and whether
        we can successfully obtain an access token.
        """
        tenant_url_configured = bool(client.config.tenant_url)

        # Try to obtain a token; any failure will be reflected in the response.
        token_ok = False
        error: str | None = None

        try:
            await client.oauth.get_access_token()
            token_ok = True
        except Exception as exc:  # noqa: BLE001
            token_ok = False
            error = str(exc)

        status = "ok" if (tenant_url_configured and token_ok) else "not_ok"

        return {
            "summary": f"Datasphere connection status: {status}",
            "data": {
                "tenant_url_configured": tenant_url_configured,
                "token_obtained": token_ok,
                "error": error,
            },
            "meta": {},
        }

    @mcp.tool()
    async def list_spaces() -> dict:
        """List all accessible Datasphere spaces.

        Returns a structured list of spaces including id, name and description.
        """
        spaces = await client.list_spaces()

        items = [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
            }
            for s in spaces
        ]

        return {
            "summary": f"Found {len(items)} Datasphere spaces.",
            "data": items,
            "meta": {
                "count": len(items),
            },
        }
