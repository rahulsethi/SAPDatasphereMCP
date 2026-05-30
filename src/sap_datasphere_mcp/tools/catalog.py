# SAP Datasphere MCP Server
# File: tools/catalog.py
# Version: v1 (1.0)

"""Catalog tier tools (facade)."""

from __future__ import annotations

from typing import Any, Awaitable, Callable, List, Tuple

from . import tasks
from ._metadata import TOOL_REGISTRY, ToolMetadata

__all__ = ["BINDINGS"]

BINDINGS: List[Tuple[ToolMetadata, Callable[..., Awaitable[Any]]]] = [
    (TOOL_REGISTRY["datasphere_catalog_list_spaces"], tasks.list_spaces),
    (TOOL_REGISTRY["datasphere_catalog_list_assets"], tasks.list_assets),
    (TOOL_REGISTRY["datasphere_catalog_get_asset"], tasks.get_asset_metadata),
    (TOOL_REGISTRY["datasphere_catalog_list_columns"], tasks.list_columns),
    (TOOL_REGISTRY["datasphere_catalog_space_overview"], tasks.space_summary),
]
