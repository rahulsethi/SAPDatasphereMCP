# SAP Datasphere MCP Server
# File: __main__.py
# Version: v1 (1.0)

"""Allow ``python -m sap_datasphere_mcp`` to start the stdio server."""

from __future__ import annotations

from .transports.stdio_server import main

if __name__ == "__main__":
    raise SystemExit(main())
