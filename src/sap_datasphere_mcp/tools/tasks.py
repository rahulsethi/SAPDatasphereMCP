# SAP Datasphere MCP Server
# File: tools/tasks.py
# Version: v12
#
# NOTE: This module is the single place where we define "business logic"
# that is exposed as MCP tools.  The MCP transports (stdio / http) simply
# call `register_tools(server)` to wire these up.

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
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


def _parse_relational_metadata_columns(
    xml_text: str,
    max_columns: int = 200,
) -> List[Dict[str, Any]]:
    """Parse an OData/EDMX $metadata document to extract column info.

    This is intentionally tolerant of namespaces: we match on tag endings
    like 'Schema', 'EntityType', 'Property', 'Key', 'PropertyRef' rather
    than relying on specific prefixes.
    """
    root = ET.fromstring(xml_text)

    # Find candidate Schema elements (any namespace).
    schemas: List[ET.Element] = []
    for elem in root.iter():
        if elem.tag.endswith("Schema"):
            schemas.append(elem)

    if not schemas:
        return []

    # Choose the first EntityType with at least one Property.
    entity_type: Optional[ET.Element] = None
    for schema in schemas:
        for child in schema:
            if child.tag.endswith("EntityType"):
                props = [p for p in child if p.tag.endswith("Property")]
                if props:
                    entity_type = child
                    break
        if entity_type is not None:
            break

    if entity_type is None:
        return []

    # Collect key property names from <Key><PropertyRef Name="..."/>.
    key_props: set[str] = set()
    for child in entity_type:
        if child.tag.endswith("Key"):
            for pref in child:
                if pref.tag.endswith("PropertyRef"):
                    name = pref.get("Name")
                    if name:
                        key_props.add(name)

    # Collect column definitions from <Property>.
    columns: List[Dict[str, Any]] = []
    for prop in entity_type:
        if not prop.tag.endswith("Property"):
            continue

        name = prop.get("Name")
        if not name:
            continue

        type_name = prop.get("Type")
        nullable_attr = prop.get("Nullable")
        nullable: Optional[bool] = None
        if nullable_attr is not None:
            nullable = nullable_attr.lower() != "false"

        is_key = name in key_props

        # For now we do not attempt to infer 'role' (dimension/measure).
        columns.append(
            {
                "name": name,
                "type": type_name,
                "nullable": nullable,
                "is_key": is_key,
                "role": None,
                "raw": None,
            }
        )

        if len(columns) >= max_columns:
            break

    return columns


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
# Metadata & discovery helpers
# ---------------------------------------------------------------------------


async def get_asset_metadata(
    space_id: str,
    asset_name: str,
) -> Dict[str, Any]:
    """Fetch catalog metadata for a single asset.

    Uses the Datasphere Catalog API single-asset endpoint. Returns a
    friendly summary plus the raw payload so that callers (or LLMs) can
    see all available fields.
    """
    client = _make_client()
    raw = await client.get_catalog_asset(space_id=space_id, asset_id=asset_name)

    asset_id = (
        raw.get("id")
        or raw.get("technicalName")
        or raw.get("name")
        or asset_name
    )
    name = raw.get("name") or raw.get("label") or asset_id
    label = raw.get("label")
    description = raw.get("description")
    asset_type = (
        raw.get("type")
        or raw.get("assetType")
        or raw.get("kind")
    )

    relational_metadata_url = raw.get("assetRelationalMetadataUrl") or raw.get(
        "relationalMetadataUrl"
    )
    relational_data_url = raw.get("assetRelationalDataUrl") or raw.get(
        "relationalDataUrl"
    )
    analytical_metadata_url = raw.get("assetAnalyticalMetadataUrl") or raw.get(
        "analyticalMetadataUrl"
    )
    analytical_data_url = raw.get("assetAnalyticalDataUrl") or raw.get(
        "analyticalDataUrl"
    )

    supports_relational = bool(relational_metadata_url or relational_data_url)
    supports_analytical = bool(analytical_metadata_url or analytical_data_url)

    return {
        "space_id": space_id,
        "asset_id": str(asset_id),
        "name": str(name) if name is not None else None,
        "label": label,
        "description": description,
        "type": str(asset_type) if asset_type is not None else None,
        "supports_relational_queries": supports_relational,
        "supports_analytical_queries": supports_analytical,
        "urls": {
            "relational_metadata": relational_metadata_url,
            "relational_data": relational_data_url,
            "analytical_metadata": analytical_metadata_url,
            "analytical_data": analytical_data_url,
        },
        "raw": raw,
    }


async def list_columns(
    space_id: str,
    asset_name: str,
    max_columns: int = 200,
) -> Dict[str, Any]:
    """List columns for an asset using relational metadata when possible.

    We try to use the relational Consumption API $metadata endpoint to get
    explicit column definitions (names, types, key flags, nullability).
    If that fails, we fall back to a tiny data preview to infer column
    names only.

    The goal is to be fast and robust rather than perfectly complete.
    """
    client = _make_client()
    columns: List[Dict[str, Any]] = []
    meta: Dict[str, Any] = {
        "space_id": space_id,
        "asset_name": asset_name,
        "source": None,
    }

    # First, try the relational metadata endpoint.
    xml_text: Optional[str] = None
    try:
        xml_text = await client.get_relational_metadata(
            space_id=space_id,
            asset_name=asset_name,
        )
    except Exception:
        xml_text = None

    if xml_text:
        try:
            columns = _parse_relational_metadata_columns(
                xml_text,
                max_columns=max_columns,
            )
            if columns:
                meta["source"] = "relational_metadata"
        except Exception:
            columns = []

    # Fallback: derive column names from a tiny preview.
    if not columns:
        preview = await preview_asset(
            space_id=space_id,
            asset_name=asset_name,
            top=1,
        )
        col_names = preview.get("columns") or []
        for name in col_names[:max_columns]:
            columns.append(
                {
                    "name": name,
                    "type": None,
                    "nullable": None,
                    "is_key": False,
                    "role": None,
                    "raw": None,
                }
            )
        meta["source"] = "sample_inference"

    meta["column_count"] = len(columns)

    return {
        "space_id": space_id,
        "asset_name": asset_name,
        "columns": columns,
        "meta": meta,
    }


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


async def find_assets_by_column(
    column_name: str,
    space_id: Optional[str] = None,
    limit: int = 100,
    max_spaces: int = 20,
    max_assets_per_space: int = 50,
) -> Dict[str, Any]:
    """Search across one or many spaces for assets exposing a column.

    The match is case-insensitive and exact on column name. We use a tiny
    preview per asset (top=1) and enforce safety caps on both the number
    of spaces and the number of assets sampled per space.
    """
    client = _make_client()
    target = column_name.lower()
    results: List[Dict[str, Any]] = []
    spaces_scanned = 0
    assets_scanned = 0

    async def scan_space(sid: str) -> None:
        nonlocal spaces_scanned, assets_scanned, results
        if len(results) >= limit:
            return

        assets = await client.list_space_assets(space_id=sid)
        spaces_scanned += 1

        checked_in_space = 0
        for a in assets:
            if checked_in_space >= max_assets_per_space:
                break
            if len(results) >= limit:
                break
            checked_in_space += 1

            try:
                qr = await client.preview_asset_data(
                    space_id=sid,
                    asset_name=a.id,
                    top=1,
                )
            except RuntimeError:
                # Not consumable / other error – skip quietly
                continue

            assets_scanned += 1
            for col_name in qr.columns:
                if col_name.lower() == target:
                    results.append(
                        {
                            "space_id": sid,
                            "asset_id": a.id,
                            "asset_name": a.name,
                            "column_name": col_name,
                            "column_count": len(qr.columns),
                        }
                    )
                    break

    if space_id:
        await scan_space(space_id)
    else:
        spaces = await client.list_spaces()
        for s in spaces:
            if spaces_scanned >= max_spaces or len(results) >= limit:
                break
            await scan_space(s.id)

    return {
        "space_id": space_id,
        "column_name": column_name,
        "limit": limit,
        "results": results,
        "stats": {
            "spaces_scanned": spaces_scanned,
            "assets_scanned": assets_scanned,
            "max_spaces": max_spaces,
            "max_assets_per_space": max_assets_per_space,
        },
    }


async def profile_column(
    space_id: str,
    asset_name: str,
    column_name: str,
    top: int = 100,
) -> Dict[str, Any]:
    """Sample-based profiling helper for a single column.

    Uses a preview sample (default 100 rows) to compute:

    - total / null / non-null counts
    - distinct count in the sample
    - a few example values
    - basic numeric stats (min, max, mean, percentiles, IQR, outlier hints)
    - basic categorical profiling (top values, frequencies)
    - a coarse role hint (id / measure / dimension)
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

    # Distinct values (for examples)
    distinct_values = []
    seen = set()
    for v in non_null_values:
        if v not in seen:
            distinct_values.append(v)
            seen.add(v)
        if len(distinct_values) >= 20:
            break

    # Type frequencies
    type_counts: Dict[str, int] = {}
    for v in non_null_values:
        t = type(v).__name__
        type_counts[t] = type_counts.get(t, 0) + 1
    ordered_types = sorted(
        type_counts.keys(), key=lambda t: type_counts[t], reverse=True
    )

    # Numeric stats (sample-based)
    numeric_summary: Optional[Dict[str, float]] = None
    numeric_like: List[float] = []

    for v in non_null_values:
        if isinstance(v, (int, float)):
            numeric_like.append(float(v))
        else:
            try:
                numeric_like.append(float(str(v)))
            except Exception:
                # If we hit non-coercible values, we simply skip them.
                continue

    if numeric_like:
        numeric_like_sorted = sorted(numeric_like)
        count = len(numeric_like_sorted)

        def _percentile(p: float) -> Optional[float]:
            if count == 0:
                return None
            if count == 1:
                return numeric_like_sorted[0]
            pos = (p / 100.0) * (count - 1)
            lower = math.floor(pos)
            upper = math.ceil(pos)
            if lower == upper:
                return numeric_like_sorted[lower]
            frac = pos - lower
            return (
                numeric_like_sorted[lower]
                + (numeric_like_sorted[upper] - numeric_like_sorted[lower]) * frac
            )

        p25 = _percentile(25.0)
        p50 = _percentile(50.0)
        p75 = _percentile(75.0)

        iqr = None
        lower_fence = None
        upper_fence = None
        outlier_count = None

        if p25 is not None and p75 is not None:
            iqr = p75 - p25
            lower_fence = p25 - 1.5 * iqr
            upper_fence = p75 + 1.5 * iqr
            outlier_count = sum(
                1
                for x in numeric_like_sorted
                if x < lower_fence or x > upper_fence
            )

        numeric_summary = {
            "min": min(numeric_like_sorted),
            "max": max(numeric_like_sorted),
            "mean": sum(numeric_like_sorted) / count if count else None,
            "p25": p25,
            "p50": p50,
            "p75": p75,
            "iqr": iqr,
            "lower_fence": lower_fence,
            "upper_fence": upper_fence,
            "outlier_count": outlier_count,
        }

    # Categorical profiling (for low-cardinality columns)
    categorical_summary: Optional[Dict[str, Any]] = None
    if non_null_values:
        freq: Dict[Any, int] = {}
        for v in non_null_values:
            freq[v] = freq.get(v, 0) + 1

        unique_values = len(freq)
        non_null_count = len(non_null_values)

        # Only emit categorical stats when cardinality is reasonably small.
        if unique_values <= 50 or unique_values <= max(1, non_null_count // 2):
            # Sort by frequency descending, then value for determinism
            sorted_items = sorted(
                freq.items(),
                key=lambda item: (-item[1], str(item[0])),
            )
            top_values = []
            for value, count_v in sorted_items[:20]:
                frac = count_v / non_null_count if non_null_count else 0.0
                top_values.append(
                    {
                        "value": value,
                        "count": count_v,
                        "fraction": frac,
                    }
                )

            concentration = (
                top_values[0]["fraction"] if top_values else None
            )

            categorical_summary = {
                "total_sampled": non_null_count,
                "unique_values": unique_values,
                "top_values": top_values,
                "concentration": concentration,
            }

    # Role hint (id / measure / dimension) – very coarse, best-effort.
    role_hint: Optional[str] = None
    non_null_count = len(non_null_values)
    distinct_non_null = len(set(non_null_values)) if non_null_values else 0
    is_numeric = bool(numeric_like)

    name_lower = column_name.lower()

    if non_null_count > 0:
        # Likely ID: name looks like an ID/key and high cardinality.
        if any(
            token in name_lower
            for token in ("id", "_id", "key", "_key")
        ) and distinct_non_null >= max(1, int(0.9 * non_null_count)):
            role_hint = "id"
        elif is_numeric:
            # Numeric but not ID-like: treat as measure when high-ish cardinality.
            if distinct_non_null > max(5, int(0.5 * non_null_count)):
                role_hint = "measure"
        else:
            # Non-numeric: low/medium cardinality looks like a dimension.
            if distinct_non_null <= max(50, int(0.7 * non_null_count)):
                role_hint = "dimension"

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
        "categorical_summary": categorical_summary,
        "role_hint": role_hint,
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

    # --- get_asset_metadata --------------------------------------------------

    @server.tool(
        name="datasphere_get_asset_metadata",
        description="Get catalog metadata for a Datasphere asset, including "
        "labels, type and exposure via relational/analytical APIs.",
    )
    async def mcp_get_asset_metadata(
        space_id: str,
        asset_name: str,
    ) -> Dict[str, Any]:
        return await get_asset_metadata(
            space_id=space_id,
            asset_name=asset_name,
        )

    # --- list_columns --------------------------------------------------------

    @server.tool(
        name="datasphere_list_columns",
        description="List columns of a Datasphere asset using relational "
        "metadata when available (with sample-based fallback).",
    )
    async def mcp_list_columns(
        space_id: str,
        asset_name: str,
        max_columns: int = 200,
    ) -> Dict[str, Any]:
        return await list_columns(
            space_id=space_id,
            asset_name=asset_name,
            max_columns=max_columns,
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

    # --- find_assets_by_column ----------------------------------------------

    @server.tool(
        name="datasphere_find_assets_by_column",
        description="Search across one or many spaces for assets that expose "
        "a given column name (case-insensitive, exact match).",
    )
    async def mcp_find_assets_by_column(
        column_name: str,
        space_id: Optional[str] = None,
        limit: int = 100,
        max_spaces: int = 20,
        max_assets_per_space: int = 50,
    ) -> Dict[str, Any]:
        return await find_assets_by_column(
            column_name=column_name,
            space_id=space_id,
            limit=limit,
            max_spaces=max_spaces,
            max_assets_per_space=max_assets_per_space,
        )

    # --- profile_column ------------------------------------------------------

    @server.tool(
        name="datasphere_profile_column",
        description="Profile a single column in an asset (nulls, distincts, "
        "basic numeric & categorical stats) using a preview sample.",
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
