# SAP Datasphere MCP Server
# File: tools/summarize.py
# Version: v1 (1.0)

"""Summarize tier tools (facade)."""

from __future__ import annotations

from typing import Any, Awaitable, Callable, List, Tuple

from . import tasks
from ._metadata import TOOL_REGISTRY, ToolMetadata

__all__ = ["BINDINGS"]

BINDINGS: List[Tuple[ToolMetadata, Callable[..., Awaitable[Any]]]] = [
    (TOOL_REGISTRY["datasphere_summarize_asset"], tasks.summarize_asset),
    (TOOL_REGISTRY["datasphere_summarize_space"], tasks.summarize_space),
    (TOOL_REGISTRY["datasphere_summarize_column_profile"], tasks.summarize_column_profile),
    (TOOL_REGISTRY["datasphere_summarize_compare_assets"], tasks.compare_assets_basic),
]
