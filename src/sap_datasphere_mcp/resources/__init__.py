# SAP Datasphere MCP Server
# File: resources/__init__.py
# Version: v1 (1.0)

"""MCP Resources package.

Exposes URI-addressable catalog content so MCP hosts can preload context
without a tool call. First-in-class for the SAP MCP ecosystem.

URI patterns (registered in :mod:`catalog_resources`):

- ``datasphere://space/{space_id}``
- ``datasphere://space/{space_id}/asset/{asset_name}``
- ``datasphere://space/{space_id}/asset/{asset_name}/schema``
- ``datasphere://space/{space_id}/asset/{asset_name}/sample``
"""

from __future__ import annotations

import logging
from typing import Any

from . import catalog_resources

__all__ = ["register"]

log = logging.getLogger("sap_datasphere_mcp.resources")


def register(server: Any) -> None:
    """Register every resource URI pattern on ``server``.

    No-ops on MCP SDKs without resource support.
    """
    if not hasattr(server, "resource"):
        log.warning("MCP server lacks .resource() — skipping resource registration; upgrade mcp[cli] for resource support.")
        return
    catalog_resources.register(server)
