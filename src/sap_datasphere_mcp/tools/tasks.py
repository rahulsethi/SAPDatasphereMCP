# SAP Datasphere MCP Server
# File: tools/tasks.py
# Version: v8

"""MCP-friendly async tasks backed by DatasphereClient.

These functions implement the core business logic and are designed to be
both:

- easy to call directly from smoke tests, and
- easy to expose as MCP tools from transports (stdio / http).

All public coroutines return only JSON-serialisable structures.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from ..auth import OAuthClient
from ..client import DatasphereClient
from ..config import DatasphereConfig


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _make_client() -> DatasphereClient:
    """Create a DatasphereClient from environment variables."""
    cfg = DatasphereConfig.from_env()
    oauth = OAuthClient(config=cfg)
    return DatasphereClient(config=cfg, oauth=oauth)


def _summarise_column_values(
    col_name: str,
    rows: List[List[Any]],
    columns: List[str],
    max_examples: int = 3,
) -> Dict[str, Any]:
    """Derive simple type + example summary for a single column."""
    try:
        idx = columns.index(col_name)
    except ValueError:
        return {
            "name": col_name,
            "types": [],
            "non_null": 0,
            "total": len(rows),
            "examples": [],
        }

    values = [row[idx] for row in rows]
    total = len(values)
    non_null_values = [v for v in values if v is not None]
    non_null = len(non_null_values)

    # Collect simple type names (str, int, float, bool, None)
    type_names = []
    for v in non_null_values:
        tname = type(v).__name__
        if tname not in type_names:
            type_names.append(tname)

    # Example values (deduplicated, up to max_examples)
    examples: List[Any] = []
    for v in non_null_values:
        if v not in examples:
            examples.append(v)
        if len(examples) >= max_examples:
            break

    return {
        "name": col_name,
        "types": type_names,
        "non_null": non_null,
        "total": total,
        "examples": examples,
    }


# ---------------------------------------------------------------------------
# Core async tasks (library-style)
# ---------------------------------------------------------------------------


async def ping() -> Dict[str, Any]:
    """Lightweight health check for the Datasphere configuration.

    Returns
    -------
    dict
        JSON-serialisable object with an ``ok`` flag.
    """
    client = _make_client()
    ok = await client.ping()
    return {"ok": bool(ok)}


async def list_spaces() -> Dict[str, Any]:
    """List SAP Datasphere spaces visible to this OAuth client.

    Returns
    -------
    dict
        {"spaces": [ {id, name, description}, ... ]}
    """
    client = _make_client()
    spaces = await client.list_spaces()

    items: List[Dict[str, Any]] = []
    for s in spaces:
        items.append(
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
            }
        )

    return {"spaces": items}


async def list_assets(space_id: str) -> Dict[str, Any]:
    """List catalog assets within a given space.

    Parameters
    ----------
    space_id:
        Technical ID / name of the Datasphere space.

    Returns
    -------
    dict
        {
          "space_id": "<space_id>",
          "assets": [
            {id, name, type, space_id, description},
            ...
          ]
        }
    """
    client = _make_client()
    assets = await client.list_space_assets(space_id=space_id)

    items: List[Dict[str, Any]] = []
    for a in assets:
        items.append(
            {
                "id": a.id,
                "name": a.name,
                "type": a.type,
                "space_id": a.space_id,
                "description": a.description,
            }
        )

    return {"space_id": space_id, "assets": items}


async def preview_asset(
    space_id: str,
    asset_name: str,
    top: int = 20,
    select: Optional[Iterable[str]] = None,
    filter_expr: Optional[str] = None,
    order_by: Optional[str] = None,
) -> Dict[str, Any]:
    """Fetch a small sample of rows from a Datasphere asset.

    Parameters
    ----------
    space_id:
        Space that owns the asset.
    asset_name:
        Technical name / ID of the asset.
    top:
        Maximum number of rows to return.
    select:
        Optional list of columns to project.
    filter_expr:
        Optional OData-style filter expression.
    order_by:
        Optional OData-style order by expression.

    Returns
    -------
    dict
        {
          "columns":  [col_name, ...],
          "rows":     [[...], [...], ...],
          "truncated": bool,
          "meta":     {...}
        }
    """
    client = _make_client()
    result = await client.preview_asset_data(
        space_id=space_id,
        asset_name=asset_name,
        top=top,
        select=select,
        filter_expr=filter_expr,
        order_by=order_by,
    )

    return {
        "columns": result.columns,
        "rows": result.rows,
        "truncated": result.truncated,
        "meta": result.meta,
    }


async def describe_asset_schema(
    space_id: str,
    asset_name: str,
    top: int = 50,
) -> Dict[str, Any]:
    """Inspect a sample of rows and infer a simple schema description.

    This is intentionally lightweight: it samples up to ``top`` rows using
    ``preview_asset_data`` and derives basic type information and examples
    for each column.

    Returns
    -------
    dict
        {
          "space_id": ...,
          "asset_name": ...,
          "row_count": int,
          "truncated": bool,
          "columns": [
            {
              "name": str,
              "types": [str],
              "non_null": int,
              "total": int,
              "examples": [...]
            },
            ...
          ]
        }
    """
    client = _make_client()
    preview = await client.preview_asset_data(
        space_id=space_id,
        asset_name=asset_name,
        top=top,
    )

    columns = preview.columns
    rows = preview.rows

    summaries: List[Dict[str, Any]] = []
    for col in columns:
        summaries.append(_summarise_column_values(col, rows, columns))

    return {
        "space_id": space_id,
        "asset_name": asset_name,
        "row_count": len(rows),
        "truncated": preview.truncated,
        "columns": summaries,
    }


async def query_relational(
    space_id: str,
    asset_name: str,
    select: Optional[Iterable[str]] = None,
    filter_expr: Optional[str] = None,
    order_by: Optional[str] = None,
    top: int = 100,
    skip: int = 0,
) -> Dict[str, Any]:
    """Run a richer relational query against a Datasphere asset.

    This uses the same relational consumption endpoint as ``preview_asset``,
    but gives you more control over paging and projection.

    Parameters
    ----------
    space_id:
        Space that owns the asset.
    asset_name:
        Technical name / ID of the asset.
    select:
        Optional iterable of column names to project.
    filter_expr:
        Optional OData-style filter expression (e.g. "SALARY gt 100").
    order_by:
        Optional OData-style order by (e.g. "HIRE_DATE desc").
    top:
        Maximum number of rows to return.
    skip:
        Number of rows to skip before returning results.

    Returns
    -------
    dict
        {
          "columns": [...],
          "rows": [[...], ...],
          "truncated": bool,
          "meta": {...}
        }
    """
    client = _make_client()
    result = await client.query_relational(
        space_id=space_id,
        asset_name=asset_name,
        select=select,
        filter_expr=filter_expr,
        order_by=order_by,
        top=top,
        skip=skip,
    )

    return {
        "columns": result.columns,
        "rows": result.rows,
        "truncated": result.truncated,
        "meta": result.meta,
    }


# ---------------------------------------------------------------------------
# MCP tool registration
# ---------------------------------------------------------------------------


def register_tools(server: Any) -> None:
    """Register MCP tools on an ``mcp.server.fastmcp.FastMCP`` instance.

    We deliberately keep this dependency-light: ``server`` is treated as a
    duck-typed object that just needs a ``.tool`` decorator.
    """

    if server is None or not hasattr(server, "tool"):
        raise ValueError(
            "register_tools(server) expects an MCP Server-like object "
            "that exposes a .tool() decorator."
        )

    # --- ping ----------------------------------------------------------------

    @server.tool(
        name="datasphere_ping",
        description="Basic health check for the SAP Datasphere MCP server.",
    )
    async def mcp_ping() -> Dict[str, Any]:
        return await ping()

    # --- list_spaces ---------------------------------------------------------

    @server.tool(
        name="datasphere_list_spaces",
        description="List SAP Datasphere spaces visible to this OAuth client.",
    )
    async def mcp_list_spaces() -> Dict[str, Any]:
        return await list_spaces()

    # --- list_assets ---------------------------------------------------------

    @server.tool(
        name="datasphere_list_assets",
        description="List catalog assets in a given SAP Datasphere space.",
    )
    async def mcp_list_assets(space_id: str) -> Dict[str, Any]:
        return await list_assets(space_id=space_id)

    # --- preview_asset -------------------------------------------------------

    @server.tool(
        name="datasphere_preview_asset",
        description="Preview a small set of rows from a Datasphere asset.",
    )
    async def mcp_preview_asset(
        space_id: str,
        asset_name: str,
        top: int = 20,
        select: Optional[List[str]] = None,
        filter_expr: Optional[str] = None,
        order_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        return await preview_asset(
            space_id=space_id,
            asset_name=asset_name,
            top=top,
            select=select,
            filter_expr=filter_expr,
            order_by=order_by,
        )

    # --- describe_asset_schema ----------------------------------------------

    @server.tool(
        name="datasphere_describe_asset_schema",
        description="Infer a simple schema for a Datasphere asset "
        "from a small data sample.",
    )
    async def mcp_describe_asset_schema(
        space_id: str,
        asset_name: str,
        top: int = 50,
    ) -> Dict[str, Any]:
        return await describe_asset_schema(
            space_id=space_id,
            asset_name=asset_name,
            top=top,
        )

    # --- query_relational ----------------------------------------------------

    @server.tool(
        name="datasphere_query_relational",
        description=(
            "Run a relational query against a Datasphere asset with "
            "optional filter/order/limit/skip."
        ),
    )
    async def mcp_query_relational(
        space_id: str,
        asset_name: str,
        top: int = 100,
        skip: int = 0,
        select: Optional[List[str]] = None,
        filter_expr: Optional[str] = None,
        order_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        return await query_relational(
            space_id=space_id,
            asset_name=asset_name,
            select=select,
            filter_expr=filter_expr,
            order_by=order_by,
            top=top,
            skip=skip,
        )

