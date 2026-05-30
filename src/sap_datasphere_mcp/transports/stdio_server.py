# SAP Datasphere MCP Server
# File: transports/stdio_server.py
# Version: v9 (1.0)

"""STDIO entrypoint for the SAP Datasphere MCP server.

Backed by :func:`sap_datasphere_mcp.server.create_server` so stdio and HTTP
boot the same way. Used by the ``sap-datasphere-mcp`` console script.
"""

from __future__ import annotations

import sys

from .. import __version__
from ..server import create_server


def main() -> int:
    """Synchronous entrypoint for console_scripts.

    Recognises a few zero-arg flags so users can sanity-check the install:

    - ``--version`` / ``-V`` — print the resolved version and exit
    - ``--help`` / ``-h`` — print a short help and exit
    """
    argv = sys.argv[1:]
    if argv:
        if argv[0] in {"--version", "-V"}:
            print(f"sap-datasphere-mcp {__version__}")
            return 0
        if argv[0] in {"--help", "-h"}:
            print(
                "sap-datasphere-mcp — read-only SAP Datasphere MCP server.\n\n"
                "Usage:\n"
                "  sap-datasphere-mcp                Start the stdio MCP server (default).\n"
                "  sap-datasphere-mcp --version      Show version and exit.\n"
                "  sap-datasphere-mcp --help         Show this help and exit.\n\n"
                "For HTTP transport use:  python -m sap_datasphere_mcp.transports.http_server\n"
                "Docs:  https://github.com/rahulsethi/SAPDatasphereMCP/blob/main/public_docs/INSTALLATION.md\n"
            )
            return 0

    mcp = create_server()
    mcp.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
