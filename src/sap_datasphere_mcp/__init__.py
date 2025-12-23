# SAP Datasphere MCP Server
# File: __init__.py
# Version: v2

"""Top-level package for the SAP Datasphere MCP Server."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

__all__ = ["__version__"]


def _resolve_version() -> str:
    """Resolve installed distribution version.

    Uses Python package metadata so __version__ stays aligned with pyproject.toml.
    Falls back to a reasonable default when running from source without an
    installed distribution.
    """
    try:
        return version("mcp-sap-datasphere-server")
    except PackageNotFoundError:
        # Running from source tree without installed package metadata.
        # This fallback avoids import-time failure.
        return "0.2.0"


__version__ = _resolve_version()
