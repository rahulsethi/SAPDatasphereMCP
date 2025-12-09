# SAP Datasphere MCP Server
# File: models.py
# Version: v1

"""Domain models used by the SAP Datasphere MCP Server."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


@dataclass
class Space:
    """A logical Datasphere space."""

    id: str
    name: str
    description: str | None = None
    raw: Mapping[str, Any] | None = None


@dataclass
class Asset:
    """A catalog asset inside a space."""

    id: str
    name: str
    space_id: str
    type: str
    description: str | None = None
    raw: Mapping[str, Any] | None = None


@dataclass
class Column:
    """A column in an asset schema."""

    name: str
    type: str
    nullable: bool = True
    is_key: bool = False
    description: str | None = None


@dataclass
class QueryResult:
    """Tabular result returned from Datasphere."""

    columns: Sequence[str]
    rows: Sequence[Sequence[Any]]
    truncated: bool = False
    row_count: int | None = None
