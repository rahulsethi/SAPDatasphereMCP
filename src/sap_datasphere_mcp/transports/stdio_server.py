# SAP Datasphere MCP Server
# File: transports/stdio_server.py
# Version: v7

"""STDIO entrypoint for the SAP Datasphere MCP server.

This is the script behind the ``sap-datasphere-mcp`` console command.

It:

- creates a FastMCP server,
- registers all Datasphere tools, and
- runs the built-in stdio transport.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from ..tools import tasks


def main() -> None:
    """Synchronous entrypoint for console_scripts."""
    mcp = FastMCP("sap-datasphere-mcp")

    # Register MCP tools (ping, list_spaces, list_assets, preview_asset, …)
    tasks.register_tools(mcp)

    # Let FastMCP handle stdio + event loop setup.
    mcp.run()


if __name__ == "__main__":
    main()

