# SAP Datasphere MCP Server
# File: tools/discover.py
# Version: v1 (1.0)

"""Discover tier tools (facade)."""

from __future__ import annotations

from typing import Any, Awaitable, Callable, List, Tuple

from . import tasks
from ._metadata import TOOL_REGISTRY, ToolMetadata

__all__ = ["BINDINGS"]

BINDINGS: List[Tuple[ToolMetadata, Callable[..., Awaitable[Any]]]] = [
    (TOOL_REGISTRY["datasphere_discover_assets"], tasks.search_assets),
    (TOOL_REGISTRY["datasphere_discover_assets_with_column"], tasks.find_assets_with_column),
    (TOOL_REGISTRY["datasphere_discover_assets_by_column"], tasks.find_assets_by_column),
]
