# SAP Datasphere MCP Server
# File: tools/connectivity.py
# Version: v1 (1.0)

"""Connectivity & diagnostics tools (facade).

Re-exports the 5 connectivity-tier async implementations from
:mod:`sap_datasphere_mcp.tools.tasks`. The category module owns only the
registration metadata + binding; tool logic lives in ``tasks.py``.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable, List, Tuple

from . import tasks
from ._metadata import TOOL_REGISTRY, ToolMetadata

__all__ = ["BINDINGS"]

#: (metadata, implementation) pairs in registration order.
BINDINGS: List[Tuple[ToolMetadata, Callable[..., Awaitable[Any]]]] = [
    (TOOL_REGISTRY["datasphere_connectivity_ping"], tasks.ping),
    (TOOL_REGISTRY["datasphere_connectivity_diagnostics"], tasks.diagnostics),
    (TOOL_REGISTRY["datasphere_connectivity_tenant_info"], tasks.get_tenant_info),
    (TOOL_REGISTRY["datasphere_connectivity_whoami"], tasks.get_current_user),
    (TOOL_REGISTRY["datasphere_connectivity_plugins_status"], tasks.plugins_status),
]
