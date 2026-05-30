# SAP Datasphere MCP Server
# File: server.py
# Version: v1 (1.0)

"""FastMCP server factory shared by both transports.

A single ``create_server()`` call:

1. Loads dotenv (if a ``.env`` is present next to the working directory).
2. Constructs a ``FastMCP("sap-datasphere-mcp")``.
3. Registers all v1.0 tools + legacy aliases via :func:`tools.registry.register_all`.
4. Registers MCP Prompts via :func:`prompts.register`.
5. Registers MCP Resources via :func:`resources.register`.
6. Loads optional plugin modules via :func:`plugins.registry.register_plugins`.

Both ``transports.stdio_server`` and ``transports.http_server`` import this
factory so they boot identically.
"""

from __future__ import annotations

import logging
import os
from typing import Any

__all__ = ["create_server"]

log = logging.getLogger("sap_datasphere_mcp.server")


def _load_dotenv_if_present() -> None:
    try:
        from dotenv import load_dotenv  # type: ignore
    except ImportError:  # pragma: no cover — python-dotenv is a hard dep at 1.0
        return
    load_dotenv()


def create_server() -> Any:
    """Build the configured FastMCP server.

    Returns the ``FastMCP`` instance — call ``.run(...)`` on it to actually
    start serving.
    """
    _load_dotenv_if_present()

    # Local import: keeps `import sap_datasphere_mcp` cheap (e.g. for `--version`).
    from mcp.server.fastmcp import FastMCP  # type: ignore

    from . import prompts as prompts_pkg
    from . import resources as resources_pkg
    from .plugins import registry as plugin_registry
    from .tools import registry as tool_registry

    mcp = FastMCP("sap-datasphere-mcp")

    tool_registry.register_all(mcp)

    try:
        prompts_pkg.register(mcp)
    except Exception as exc:  # pragma: no cover — prompts must never break boot
        log.warning("prompts.register failed (continuing): %s", exc)

    try:
        resources_pkg.register(mcp)
    except Exception as exc:  # pragma: no cover — resources must never break boot
        log.warning("resources.register failed (continuing): %s", exc)

    try:
        plugin_registry.register_plugins(mcp)
    except Exception as exc:  # pragma: no cover — plugin failures must never break boot
        log.warning("plugin_registry.register_plugins failed (continuing): %s", exc)

    return mcp
