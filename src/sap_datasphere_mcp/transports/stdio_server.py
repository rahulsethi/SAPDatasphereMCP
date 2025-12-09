# SAP Datasphere MCP Server
# File: transports/stdio_server.py
# Version: v1

"""Entry point for running the MCP server over stdio."""

from __future__ import annotations

import logging
import sys

from mcp.server.fastmcp import FastMCP  # type: ignore[import]

from ..config import DatasphereConfig
from ..auth import OAuthClient
from ..client import DatasphereClient
from ..tools import register_all_tools


logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    """Configure basic logging to stderr.

    Important: stdio MCP servers must not write to stdout.
    """
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stderr,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def main() -> None:
    """CLI entry point for stdio transport."""
    _configure_logging()

    config = DatasphereConfig.from_env()
    oauth_client = OAuthClient(config=config)
    datasphere_client = DatasphereClient(config=config, oauth=oauth_client)

    mcp = FastMCP("sap-datasphere-mcp")
    register_all_tools(mcp, datasphere_client)

    # Blocking call: listens for MCP messages on stdin/stdout
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
