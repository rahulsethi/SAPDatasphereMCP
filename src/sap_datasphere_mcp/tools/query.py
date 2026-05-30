# SAP Datasphere MCP Server
# File: tools/query.py
# Version: v1 (1.0)

"""Query tier tools (facade)."""

from __future__ import annotations

from typing import Any, Awaitable, Callable, List, Tuple

from . import tasks
from ._metadata import TOOL_REGISTRY, ToolMetadata

__all__ = ["BINDINGS"]

BINDINGS: List[Tuple[ToolMetadata, Callable[..., Awaitable[Any]]]] = [
    (TOOL_REGISTRY["datasphere_query_preview"], tasks.preview_asset),
    (TOOL_REGISTRY["datasphere_query_relational"], tasks.query_relational),
    (TOOL_REGISTRY["datasphere_query_analytical"], tasks.query_analytical),
]
