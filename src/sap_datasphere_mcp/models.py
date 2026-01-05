# SAP Datasphere MCP Server
# File: models.py
# Version: v3

"""Domain models used by the SAP Datasphere MCP server.

Alignment notes (v0.3+):
- QueryResult.meta is treated as a dict throughout the codebase (tasks/client).
  To avoid None-related surprises, we normalize meta to {} in __post_init__.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Space:
    """Represents a Datasphere space as returned by the Catalog API."""

    id: str
    name: str
    description: Optional[str] = None

    # Raw JSON payload from the API, for debugging / advanced use.
    raw: Optional[Dict[str, Any]] = None


@dataclass
class Asset:
    """Represents a catalog asset inside a Datasphere space."""

    id: str
    name: str
    type: Optional[str] = None
    space_id: Optional[str] = None
    description: Optional[str] = None

    # Raw JSON payload from the API, for debugging / advanced use.
    raw: Optional[Dict[str, Any]] = None


@dataclass
class QueryResult:
    """Generic tabular result for data preview / queries."""

    columns: List[str]
    rows: List[List[Any]]

    # True if the result was truncated (e.g. due to row limits).
    truncated: bool = False

    # Extra metadata – timings, row counts, mode (relational/analytical), etc.
    meta: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Defensive normalization: allow older callers that passed meta=None.
        if self.meta is None:  # type: ignore[truthy-bool]
            self.meta = {}
