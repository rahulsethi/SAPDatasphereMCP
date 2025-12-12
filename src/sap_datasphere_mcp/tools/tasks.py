# SAP Datasphere MCP Server
# File: tools/tasks.py
# Version: v9
#
# NOTE: This module is the single place where we define "business logic"
# that is exposed as MCP tools.  The MCP transports (stdio / http) simply
# call `register_tools(server)` to wire these up.

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from ..auth import OAuthClient
from ..client import DatasphereClient
from ..config import DatasphereConfig


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------


def _make_client() -> DatasphereClient:
    """Create a DatasphereClient from environment variables."""
    cfg = DatasphereConfig.from_env()
    oauth = OAuthClient(config=cfg)
    return DatasphereClient(config=cfg, oauth=oauth)


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
        Optional list of column names to select.
    filter_expr:
        Optional OData-style filter expression.
    order_by:
        Optional OData-style order-by expression.

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
    top: int = 20,
) -> Dict[str, Any]:
    """Infer a simple column-oriented schema from a preview sample.

    The goal is to give an LLM (or human) just enough signal to talk about
    the asset: column names, rough Python types, null counts and a few
    example values.

    This is intentionally *sample-based* and fast; it is not a full
    metadata inspection.
    """
    # Reuse the preview task so behaviour stays consistent.
    preview = await preview_asset(
        space_id=space_id,
        asset_name=asset_name,
        top=top,
    )

    columns = preview["columns"]
    rows = preview["rows"]

    # If we have no rows, we still want to emit column names if possible.
    # In that case we fall back to a very lightweight preview with top=1
    # to discover columns.
    if not rows and not columns:
        client = _make_client()
        qr = await client.preview_asset_data(
            space_id=space_id,
            asset_name=asset_name,
            top=1,
        )
        columns = qr.columns
        rows = qr.rows

    row_count = len(rows)
    column_summaries: List[Dict[str, Any]] = []

    for col_index, col_name in enumerate(columns):
        values = [row[col_index] for row in rows if col_index < len(row)]

        total = len(values)
        non_null_values = [v for v in values if v is not None]
        non_null_count = len(non_null_values)

        type_counts: Dict[str, int] = {}
        for v in non_null_values:
            t = type(v).__name__
            type_counts[t] = type_counts.get(t, 0) + 1

        # Sort types by frequency, most common first
        ordered_types = sorted(
            type_counts.keys(), key=lambda t: type_counts[t], reverse=True
        )

        # Small set of distinct examples, preserving order
        example_values: List[Any] = []
        seen_examples = set()
        for v in values:
            if v not in seen_examples:
                example_values.append(v)
                seen_examples.add(v)
            if len(example_values) >= 5:
                break

        column_summaries.append(
            {
                "name": col_name,
                "python_types": ordered_types or None,
                "nonnull_count": non_null_count if total else None,
                "total_count": total if total else None,
                "example_values": example_values or None,
            }
        )

    meta = {
        "space_id": space_id,
        "asset_name": asset_name,
        "row_count": row_count if row_count else None,
        "top": top,
        "truncated": bool(preview.get("truncated")),
    }

    return {
        "space_id": space_id,
        "asset_name": asset_name,
        "columns": column_summaries,
        "meta": meta,
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
    """Run a richer relational query using the Consumption API.

    This is a light wrapper around ``DatasphereClient.query_relational``.
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

    meta = dict(result.meta)
    # Ensure we always surface the query-shaping knobs in meta
    meta.setdefault("top", top)
    meta.setdefault("skip", skip)
    meta.setdefault("filter", filter_expr)
    meta.setdefault("order_by", order_by)

    return {
        "columns": result.columns,
        "rows": result.rows,
        "truncated": result.truncated,
        "meta": meta,
    }


# ---------------------------------------------------------------------------
# Discovery helpers (low-hanging fruit)
# ---------------------------------------------------------------------------


async def search_assets(
    space_id: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = 100,
) -> Dict[str, Any]:
    """Search for assets by partial name / id / description / type.

    Parameters
    ----------
    space_id:
        If provided, restrict search to this space. If omitted, all visible
        spaces are scanned (which may be slower).
    query:
        Case-insensitive substring to match against asset id, name,
        description or type. If omitted, all assets are returned (up to
        ``limit``).
    limit:
        Maximum number of matching assets to return.

    Returns
    -------
    dict
        {
          "space_id": optional space filter,
          "query": query,
          "limit": limit,
          "results": [...],
          "stats": {
            "spaces_scanned": int,
            "assets_scanned": int
          }
        }
    """
    client = _make_client()
    results: List[Dict[str, Any]] = []
    spaces_scanned = 0
    assets_scanned = 0

    needle = query.lower() if query else None

    async def scan_space(sid: str) -> None:
        nonlocal spaces_scanned, assets_scanned, results
        assets = await client.list_space_assets(space_id=sid)
        spaces_scanned += 1

        for a in assets:
            assets_scanned += 1

            if needle:
                haystack_parts = [
                    a.id or "",
                    a.name or "",
                    a.description or "",
                    a.type or "",
                ]
                haystack = " ".join(str(p) for p in haystack_parts).lower()
                if needle not in haystack:
                    continue

            results.append(
                {
                    "id": a.id,
                    "name": a.name,
                    "type": a.type,
                    "space_id": a.space_id,
                    "description": a.description,
                }
            )

            if len(results) >= limit:
                return

    if space_id:
        await scan_space(space_id)
    else:
        spaces = await client.list_spaces()
        for s in spaces:
            await scan_space(s.id)
            if len(results) >= limit:
                break

    return {
        "space_id": space_id,
        "query": query,
        "limit": limit,
        "results": results,
        "stats": {
            "spaces_scanned": spaces_scanned,
            "assets_scanned": assets_scanned,
        },
    }


async def space_summary(
    space_id: str,
    max_assets: int = 50,
) -> Dict[str, Any]:
    """Summarise the assets within a single space.

    Provides total counts and a small sample list of assets with id, name
    and type. Intended to give an LLM a quick overview of a space.
    """
    client = _make_client()
    assets = await client.list_space_assets(space_id=space_id)

    type_counts: Dict[str, int] = {}
    for a in assets:
        t = a.type or "<unknown>"
        type_counts[t] = type_counts.get(t, 0) + 1

    sample_assets: List[Dict[str, Any]] = []
    for a in assets[:max_assets]:
        sample_assets.append(
            {
                "id": a.id,
                "name": a.name,
                "type": a.type,
                "description": a.description,
            }
        )

    return {
        "space_id": space_id,
        "total_assets": len(assets),
        "asset_types": type_counts,
        "sample_assets": sample_assets,
    }


async def find_assets_with_column(
    space_id: str,
    column_name: str,
    max_assets: int = 50,
) -> Dict[str, Any]:
    """Find assets in a space that expose a given column name.

    The match is case-insensitive and exact on column name. We sample up to
    ``max_assets`` assets in the space and attempt a tiny preview on each.
    Assets that are not consumable (403/404 etc.) are skipped.
    """
    client = _make_client()
    assets = await client.list_space_assets(space_id=space_id)

    target = column_name.lower()
    checked = 0
    matches: List[Dict[str, Any]] = []

    for a in assets:
        if checked >= max_assets:
            break
        checked += 1

        try:
            qr = await client.preview_asset_data(
                space_id=space_id,
                asset_name=a.id,
                top=1,
            )
        except RuntimeError:
            # Not consumable / other error – skip quietly
            continue

        for col_name in qr.columns:
            if col_name.lower() == target:
                matches.append(
                    {
                        "asset_id": a.id,
                        "asset_name": a.name,
                        "space_id": space_id,
                        "column_name": col_name,
                        "column_count": len(qr.columns),
                    }
                )
                break

    return {
        "space_id": space_id,
        "column_name": column_name,
        "max_assets": max_assets,
        "assets_checked": checked,
        "matches": matches,
    }


async def profile_column(
    space_id: str,
    asset_name: str,
    column_name: str,
    top: int = 100,
) -> Dict[str, Any]:
    """Simple data-profiling helper for a single column.

    Uses a preview sample (default 100 rows) to compute:

    - total / null / non-null counts
    - distinct count in the sample
    - a few example values
    - very basic numeric stats (min, max, mean) when applicable
    """
    client = _make_client()
    qr = await client.preview_asset_data(
        space_id=space_id,
        asset_name=asset_name,
        top=top,
        select=[column_name],
    )

    if not qr.columns:
        raise RuntimeError(
            f"Preview for asset '{asset_name}' in space '{space_id}' "
            "returned no columns."
        )

    # We requested only one column, so it should be at index 0.
    values = [row[0] for row in qr.rows if row]

    total = len(values)
    non_null_values = [v for v in values if v is not None]
    null_count = total - len(non_null_values)

    distinct_values = []
    seen = set()
    for v in non_null_values:
        if v not in seen:
            distinct_values.append(v)
            seen.add(v)
        if len(distinct_values) >= 20:
            break

    type_counts: Dict[str, int] = {}
    for v in non_null_values:
        t = type(v).__name__
        type_counts[t] = type_counts.get(t, 0) + 1
    ordered_types = sorted(
        type_counts.keys(), key=lambda t: type_counts[t], reverse=True
    )

    numeric_summary: Optional[Dict[str, float]] = None
    # Treat int / float as numeric; try best-effort coercion for strings.
    numeric_like: List[float] = []
    for v in non_null_values:
        if isinstance(v, (int, float)):
            numeric_like.append(float(v))
        else:
            try:
                numeric_like.append(float(str(v)))
            except Exception:
                numeric_like = []
                break

    if numeric_like:
        count = len(numeric_like)
        numeric_summary = {
            "min": min(numeric_like),
            "max": max(numeric_like),
            "mean": sum(numeric_like) / count if count else None,
        }

    meta = {
        "space_id": space_id,
        "asset_name": asset_name,
        "column_name": column_name,
        "sample_rows": total,
        "truncated": qr.truncated,
        "top": top,
    }

    return {
        "column": column_name,
        "types": ordered_types or None,
        "total_count": total,
        "null_count": null_count,
        "non_null_count": total - null_count,
        "distinct_sampled": len(distinct_values),
        "example_values": distinct_values or None,
        "numeric_summary": numeric_summary,
        "meta": meta,
    }


# ---------------------------------------------------------------------------
# MCP tool registration
# ---------------------------------------------------------------------------


def register_tools(server: Any) -> None:
    """Register MCP tools on an ``mcp.server.Server`` / ``FastMCP`` instance.

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
        select: Optional[Iterable[str]] = None,
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
        description="Infer column-oriented schema for a Datasphere asset "
        "from a small preview sample.",
    )
    async def mcp_describe_asset_schema(
        space_id: str,
        asset_name: str,
        top: int = 20,
    ) -> Dict[str, Any]:
        return await describe_asset_schema(
            space_id=space_id,
            asset_name=asset_name,
            top=top,
        )

    # --- query_relational ----------------------------------------------------

    @server.tool(
        name="datasphere_query_relational",
        description="Run a relational query (select / filter / order / paging) "
        "against a Datasphere asset.",
    )
    async def mcp_query_relational(
        space_id: str,
        asset_name: str,
        select: Optional[Iterable[str]] = None,
        filter_expr: Optional[str] = None,
        order_by: Optional[str] = None,
        top: int = 100,
        skip: int = 0,
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

    # --- search_assets -------------------------------------------------------

    @server.tool(
        name="datasphere_search_assets",
        description="Search for assets by partial name / id / description / "
        "type, optionally restricted to a single space.",
    )
    async def mcp_search_assets(
        space_id: Optional[str] = None,
        query: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        return await search_assets(
            space_id=space_id,
            query=query,
            limit=limit,
        )

    # --- space_summary -------------------------------------------------------

    @server.tool(
        name="datasphere_space_summary",
        description="Summarise assets in a space (counts by type plus a "
        "small sample list).",
    )
    async def mcp_space_summary(
        space_id: str,
        max_assets: int = 50,
    ) -> Dict[str, Any]:
        return await space_summary(space_id=space_id, max_assets=max_assets)

    # --- find_assets_with_column --------------------------------------------

    @server.tool(
        name="datasphere_find_assets_with_column",
        description="Find assets in a space that expose a given column name "
        "(case-insensitive, exact match).",
    )
    async def mcp_find_assets_with_column(
        space_id: str,
        column_name: str,
        max_assets: int = 50,
    ) -> Dict[str, Any]:
        return await find_assets_with_column(
            space_id=space_id,
            column_name=column_name,
            max_assets=max_assets,
        )

    # --- profile_column ------------------------------------------------------

    @server.tool(
        name="datasphere_profile_column",
        description="Profile a single column in an asset (nulls, distincts, "
        "basic numeric stats) using a preview sample.",
    )
    async def mcp_profile_column(
        space_id: str,
        asset_name: str,
        column_name: str,
        top: int = 100,
    ) -> Dict[str, Any]:
        return await profile_column(
            space_id=space_id,
            asset_name=asset_name,
            column_name=column_name,
            top=top,
        )
