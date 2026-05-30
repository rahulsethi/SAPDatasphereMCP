# SAP Datasphere MCP Server
# File: __init__.py
# Version: v4 (1.0)

"""Top-level package for the SAP Datasphere MCP Server."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

__all__ = ["__version__"]


def _resolve_version() -> str:
    """Resolve installed distribution version.

    Tries the new v1.0+ distribution name first, then the v0.3.x legacy name as
    a fallback for users who upgraded in-place without uninstalling. Final
    fallback is a hard-coded constant so source checkouts still report a
    sensible version.
    """
    for dist_name in ("sap-datasphere-mcp", "mcp-sap-datasphere-server"):
        try:
            return version(dist_name)
        except PackageNotFoundError:
            continue
    return "1.0.0"


__version__ = _resolve_version()
