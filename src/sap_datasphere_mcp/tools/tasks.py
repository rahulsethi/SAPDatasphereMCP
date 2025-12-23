# SAP Datasphere MCP Server
# File: tools/tasks.py
# Version: v16
#
# NOTE: This module is the single place where we define "business logic"
# that is exposed as MCP tools.  The MCP transports (stdio / http) simply
# call `register_tools(server)` to wire these up.

from __future__ import annotations

import math
import os
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse

from ..auth import OAuthClient
from ..cache import TTLCache
from ..client import DatasphereClient
from ..config import DatasphereConfig
from ..plugins import registry as plugin_registry


# ---------------------------------------------------------------------------
# Internal helpers (env flags, mock client, metadata parser)
# ---------------------------------------------------------------------------


def _env_flag(name: str, default: bool = False) -> bool:
    """Parse a boolean-like environment variable.

    Accepts 1/0, true/false, yes/no, on/off (case-insensitive).
    """
    val = os.getenv(name)
    if val is None:
        return default
    return str(val).strip().lower() in {"1", "true", "yes", "on"}


def _make_error(
    code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Small, LLM-friendly error shape used by diagnostics."""
    err: Dict[str, Any] = {"code": code, "message": message}
    if details:
        err["details"] = details
    return err


def _cap_int(value: int, cap: int, min_value: int = 1) -> tuple[int, bool]:
    """Clamp an integer to [min_value, cap]. Returns (effective, cap_applied)."""
    try:
        v = int(value)
    except Exception:
        v = min_value

    if v < min_value:
        v = min_value
        return v, True

    if cap > 0 and v > cap:
        return cap, True

    return v, False


_CACHE: TTLCache | None = None
_CACHE_SIGNATURE: tuple[int, int] | None = None


def _get_cache(cfg: DatasphereConfig) -> TTLCache:
    """Lazily create (or re-create) the global TTL cache based on config."""
    global _CACHE, _CACHE_SIGNATURE

    signature = (int(cfg.cache_ttl_seconds), int(cfg.cache_max_entries))
    if _CACHE is None or _CACHE_SIGNATURE != signature:
        _CACHE = TTLCache(ttl_seconds=signature[0], max_entries=signature[1])
        _CACHE_SIGNATURE = signature
    return _CACHE


@dataclass
class _MockSpace:
    id: str
    name: str
    description: str


@dataclass
class _MockAsset:
    id: str
    name: str
    type: str
    space_id: str
    description: str


@dataclass
class _MockQueryResult:
    columns: List[str]
    rows: List[List[Any]]
    truncated: bool
    meta: Dict[str, Any]


class MockDatasphereClient:
    """Small in-memory stand-in for DatasphereClient.

    Activated when DATASPHERE_MOCK_MODE is truthy. Implements the subset of
    methods used by tasks below so tools work without a real Datasphere tenant.
    """

    def __init__(self, config: Optional[DatasphereConfig] = None) -> None:
        self._config = config

        self._spaces: List[_MockSpace] = [
            _MockSpace(
                id="MOCK_SALES",
                name="Mock Sales Analytics",
                description="Static demo space for MCP mock mode.",
            ),
            _MockSpace(
                id="MOCK_FINANCE",
                name="Mock Finance",
                description="Static finance demo space for MCP mock mode.",
            ),
        ]

        self._assets_by_space: Dict[str, List[_MockAsset]] = {
            "MOCK_SALES": [
                _MockAsset(
                    id="SALES_ORDERS",
                    name="Sales Orders",
                    type="TABLE",
                    space_id="MOCK_SALES",
                    description="Mock sales orders fact table.",
                ),
                _MockAsset(
                    id="CUSTOMERS",
                    name="Customers",
                    type="TABLE",
                    space_id="MOCK_SALES",
                    description="Mock customer dimension.",
                ),
            ],
            "MOCK_FINANCE": [
                _MockAsset(
                    id="GL_BALANCES",
                    name="GL Balances",
                    type="TABLE",
                    space_id="MOCK_FINANCE",
                    description="Mock GL balances fact table.",
                ),
            ],
        }

        self._data: Dict[tuple[str, str], Dict[str, Any]] = {
            ("MOCK_SALES", "SALES_ORDERS"): {
                "columns": ["ORDER_ID", "CUSTOMER_ID", "AMOUNT"],
                "rows": [
                    [1, "CUST_1", 100.0],
                    [2, "CUST_2", 200.0],
                    [3, "CUST_1", 150.0],
                    [4, "CUST_3", 75.0],
                    [5, "CUST_2", 500.0],
                ],
            },
            ("MOCK_SALES", "CUSTOMERS"): {
                "columns": ["CUSTOMER_ID", "NAME", "COUNTRY"],
                "rows": [
                    ["CUST_1", "Alice", "DE"],
                    ["CUST_2", "Bob", "US"],
                    ["CUST_3", "Charlie", "IN"],
                ],
            },
            ("MOCK_FINANCE", "GL_BALANCES"): {
                "columns": ["GL_ACCOUNT", "FISCAL_YEAR", "AMOUNT"],
                "rows": [
                    ["400000", 2023, 100000.0],
                    ["400000", 2024, 120000.0],
                    ["800000", 2024, -50000.0],
                ],
            },
        }

        self._catalog_by_key: Dict[tuple[str, str], Dict[str, Any]] = {
            ("MOCK_SALES", "SALES_ORDERS"): {
                "id": "SALES_ORDERS",
                "name": "Sales Orders",
                "label": "Sales Orders (Mock)",
                "description": "Mock sales orders fact table.",
                "type": "VIEW",
                "assetRelationalMetadataUrl": "/mock/sales_orders/$metadata",
                "assetRelationalDataUrl": "/mock/sales_orders/data",
            },
            ("MOCK_SALES", "CUSTOMERS"): {
                "id": "CUSTOMERS",
                "name": "Customers",
                "label": "Customers (Mock)",
                "description": "Mock customer dimension.",
                "type": "VIEW",
                "assetRelationalMetadataUrl": "/mock/customers/$metadata",
                "assetRelationalDataUrl": "/mock/customers/data",
            },
            ("MOCK_FINANCE", "GL_BALANCES"): {
                "id": "GL_BALANCES",
                "name": "GL Balances",
                "label": "GL Balances (Mock)",
                "description": "Mock GL balances fact table.",
                "type": "VIEW",
                "assetRelationalMetadataUrl": "/mock/gl_balances/$metadata",
                "assetRelationalDataUrl": "/mock/gl_balances/data",
            },
        }

        self._relational_metadata_xml: str = """<?xml version="1.0" encoding="utf-8"?>
<edmx:Edmx xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx">
  <edmx:DataServices>
    <Schema Namespace="Mock" xmlns="http://docs.oasis-open.org/odata/ns/edm">
      <EntityType Name="Main">
        <Key>
          <PropertyRef Name="ORDER_ID" />
        </Key>
        <Property Name="ORDER_ID" Type="Edm.Int64" Nullable="false" />
        <Property Name="CUSTOMER_ID" Type="Edm.String" Nullable="false" />
        <Property Name="AMOUNT" Type="Edm.Decimal" Nullable="false" />
      </EntityType>
    </Schema>
  </edmx:DataServices>
</edmx:Edmx>
"""

    async def ping(self) -> bool:
        return True

    async def list_spaces(self) -> List[_MockSpace]:
        return list(self._spaces)

    async def list_space_assets(self, space_id: str) -> List[_MockAsset]:
        return list(self._assets_by_space.get(space_id, []))

    async def preview_asset_data(
        self,
        space_id: str,
        asset_name: str,
        top: int = 20,
        select: Optional[Iterable[str]] = None,
        filter_expr: Optional[str] = None,
        order_by: Optional[str] = None,
    ) -> _MockQueryResult:
        key = (space_id, asset_name)
        data = self._data.get(key)
        if not data:
            return _MockQueryResult(
                columns=[],
                rows=[],
                truncated=False,
                meta={"space_id": space_id, "asset_name": asset_name, "mock": True},
            )

        base_cols = data["columns"]
        base_rows = data["rows"]

        limit = top if top is not None else len(base_rows)
        rows_slice = base_rows[:limit]

        if select:
            select_names = [c for c in select if c in base_cols]
            indices = [base_cols.index(c) for c in select_names]
            rows_slice = [[row[i] for i in indices] for row in rows_slice]
            used_cols = select_names
        else:
            used_cols = list(base_cols)
            rows_slice = [list(r) for r in rows_slice]

        truncated = len(rows_slice) < len(base_rows)
        meta = {
            "space_id": space_id,
            "asset_name": asset_name,
            "mock": True,
            "top": top,
            "filter": filter_expr,
            "order_by": order_by,
        }
        return _MockQueryResult(columns=used_cols, rows=rows_slice, truncated=truncated, meta=meta)

    async def query_relational(
        self,
        space_id: str,
        asset_name: str,
        select: Optional[Iterable[str]] = None,
        filter_expr: Optional[str] = None,
        order_by: Optional[str] = None,
        top: int = 100,
        skip: int = 0,
    ) -> _MockQueryResult:
        key = (space_id, asset_name)
        data = self._data.get(key)
        if not data:
            return _MockQueryResult(
                columns=[],
                rows=[],
                truncated=False,
                meta={"space_id": space_id, "asset_name": asset_name, "mock": True},
            )

        base_cols = data["columns"]
        base_rows = data["rows"]

        start = max(skip or 0, 0)
        end = start + (top if top is not None else len(base_rows))
        rows_slice = base_rows[start:end]

        if select:
            select_names = [c for c in select if c in base_cols]
            indices = [base_cols.index(c) for c in select_names]
            rows_slice = [[row[i] for i in indices] for row in rows_slice]
            used_cols = select_names
        else:
            used_cols = list(base_cols)
            rows_slice = [list(r) for r in rows_slice]

        truncated = end < len(base_rows)
        meta = {
            "space_id": space_id,
            "asset_name": asset_name,
            "mock": True,
            "top": top,
            "skip": skip,
            "filter": filter_expr,
            "order_by": order_by,
        }
        return _MockQueryResult(columns=used_cols, rows=rows_slice, truncated=truncated, meta=meta)

    async def get_catalog_asset(self, space_id: str, asset_id: str) -> Dict[str, Any]:
        key = (space_id, asset_id)
        payload = self._catalog_by_key.get(key)
        if not payload:
            raise RuntimeError(f"Unknown mock asset '{asset_id}' in space '{space_id}'.")
        return payload

    async def get_relational_metadata(
        self,
        space_id: str,
        asset_name: str,
    ) -> Optional[str]:
        if (space_id, asset_name) in self._data:
            return self._relational_metadata_xml
        return None


def _make_client(cfg: Optional[DatasphereConfig] = None) -> DatasphereClient:
    """Create a DatasphereClient from environment variables.

    If DATASPHERE_MOCK_MODE is truthy, a lightweight in-process mock client
    is returned instead of a real HTTP client.

    Note: Callers should prefer invoking this with *no arguments* to keep
    unit tests monkeypatch-friendly (tests often replace _make_client with
    a no-arg lambda).
    """
    cfg = cfg or DatasphereConfig.from_env()

    if cfg.mock_mode or _env_flag("DATASPHERE_MOCK_MODE", False):
        return MockDatasphereClient(config=cfg)  # type: ignore[return-value]

    oauth = OAuthClient(config=cfg)
    return DatasphereClient(config=cfg, oauth=oauth)


def _parse_relational_metadata_columns(
    xml_text: str,
    max_columns: int = 200,
) -> List[Dict[str, Any]]:
    """Parse an OData/EDMX $metadata document to extract column info."""
    root = ET.fromstring(xml_text)

    schemas: List[ET.Element] = []
    for elem in root.iter():
        if elem.tag.endswith("Schema"):
            schemas.append(elem)

    if not schemas:
        return []

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

    key_props: set[str] = set()
    for child in entity_type:
        if child.tag.endswith("Key"):
            for pref in child:
                if pref.tag.endswith("PropertyRef"):
                    name = pref.get("Name")
                    if name:
                        key_props.add(name)

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
    client = _make_client()
    ok = await client.ping()
    return {"ok": bool(ok)}


async def list_spaces() -> Dict[str, Any]:
    cfg = DatasphereConfig.from_env()
    cache = _get_cache(cfg)
    cache_key = ("list_spaces", id(_make_client), cfg.tenant_url, cfg.mock_mode)

    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    client = _make_client()
    spaces = await client.list_spaces()

    items: List[Dict[str, Any]] = []
    for s in spaces:
        items.append({"id": s.id, "name": s.name, "description": s.description})

    out = {"spaces": items}
    cache.set(cache_key, out)
    return out


async def list_assets(space_id: str) -> Dict[str, Any]:
    cfg = DatasphereConfig.from_env()
    cache = _get_cache(cfg)
    cache_key = ("list_assets", id(_make_client), cfg.tenant_url, cfg.mock_mode, space_id)

    cached = cache.get(cache_key)
    if cached is not None:
        return cached

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

    out = {"space_id": space_id, "assets": items}
    cache.set(cache_key, out)
    return out


async def preview_asset(
    space_id: str,
    asset_name: str,
    top: int = 20,
    select: Optional[Iterable[str]] = None,
    filter_expr: Optional[str] = None,
    order_by: Optional[str] = None,
) -> Dict[str, Any]:
    cfg = DatasphereConfig.from_env()
    requested_top = top
    effective_top, cap_applied = _cap_int(top, cfg.max_rows_preview, min_value=1)

    client = _make_client()
    result = await client.preview_asset_data(
        space_id=space_id,
        asset_name=asset_name,
        top=effective_top,
        select=select,
        filter_expr=filter_expr,
        order_by=order_by,
    )

    meta = dict(result.meta)
    meta.setdefault("requested_top", requested_top)
    meta.setdefault("effective_top", effective_top)
    meta.setdefault("cap_top", cfg.max_rows_preview)
    meta.setdefault("cap_applied", bool(cap_applied))

    return {
        "columns": result.columns,
        "rows": result.rows,
        "truncated": result.truncated,
        "meta": meta,
    }


async def describe_asset_schema(
    space_id: str,
    asset_name: str,
    top: int = 20,
) -> Dict[str, Any]:
    preview = await preview_asset(space_id=space_id, asset_name=asset_name, top=top)

    columns = preview["columns"]
    rows = preview["rows"]

    if not rows and not columns:
        client = _make_client()
        qr = await client.preview_asset_data(space_id=space_id, asset_name=asset_name, top=1)
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

        ordered_types = sorted(type_counts.keys(), key=lambda t: type_counts[t], reverse=True)

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
    cfg = DatasphereConfig.from_env()
    requested_top = top
    effective_top, cap_applied = _cap_int(top, cfg.max_rows_query, min_value=1)

    client = _make_client()
    result = await client.query_relational(
        space_id=space_id,
        asset_name=asset_name,
        select=select,
        filter_expr=filter_expr,
        order_by=order_by,
        top=effective_top,
        skip=skip,
    )

    meta = dict(result.meta)
    meta.setdefault("top", effective_top)
    meta.setdefault("skip", skip)
    meta.setdefault("filter", filter_expr)
    meta.setdefault("order_by", order_by)

    meta.setdefault("requested_top", requested_top)
    meta.setdefault("effective_top", effective_top)
    meta.setdefault("cap_top", cfg.max_rows_query)
    meta.setdefault("cap_applied", bool(cap_applied))

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
    cfg = DatasphereConfig.from_env()
    cache = _get_cache(cfg)
    cache_key = ("get_asset_metadata", id(_make_client), cfg.tenant_url, cfg.mock_mode, space_id, asset_name)

    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    client = _make_client()
    raw = await client.get_catalog_asset(space_id=space_id, asset_id=asset_name)

    asset_id = raw.get("id") or raw.get("technicalName") or raw.get("name") or asset_name
    name = raw.get("name") or raw.get("label") or asset_id
    label = raw.get("label")
    description = raw.get("description")
    asset_type = raw.get("type") or raw.get("assetType") or raw.get("kind")

    relational_metadata_url = raw.get("assetRelationalMetadataUrl") or raw.get("relationalMetadataUrl")
    relational_data_url = raw.get("assetRelationalDataUrl") or raw.get("relationalDataUrl")
    analytical_metadata_url = raw.get("assetAnalyticalMetadataUrl") or raw.get("analyticalMetadataUrl")
    analytical_data_url = raw.get("assetAnalyticalDataUrl") or raw.get("analyticalDataUrl")

    supports_relational = bool(relational_metadata_url or relational_data_url)
    supports_analytical = bool(analytical_metadata_url or analytical_data_url)

    out = {
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

    cache.set(cache_key, out)
    return out


async def list_columns(
    space_id: str,
    asset_name: str,
    max_columns: int = 200,
) -> Dict[str, Any]:
    cfg = DatasphereConfig.from_env()
    cache = _get_cache(cfg)
    cache_key = ("list_columns", id(_make_client), cfg.tenant_url, cfg.mock_mode, space_id, asset_name, int(max_columns))

    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    client = _make_client()
    columns: List[Dict[str, Any]] = []
    meta: Dict[str, Any] = {
        "space_id": space_id,
        "asset_name": asset_name,
        "source": None,
    }

    xml_text: Optional[str] = None
    try:
        xml_text = await client.get_relational_metadata(space_id=space_id, asset_name=asset_name)
    except Exception:
        xml_text = None

    if xml_text:
        try:
            columns = _parse_relational_metadata_columns(xml_text, max_columns=max_columns)
            if columns:
                meta["source"] = "relational_metadata"
        except Exception:
            columns = []

    if not columns:
        preview = await preview_asset(space_id=space_id, asset_name=asset_name, top=1)
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

    out = {"space_id": space_id, "asset_name": asset_name, "columns": columns, "meta": meta}
    cache.set(cache_key, out)
    return out


async def search_assets(
    space_id: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = 100,
) -> Dict[str, Any]:
    cfg = DatasphereConfig.from_env()
    requested_limit = limit
    effective_limit, cap_applied = _cap_int(limit, cfg.max_search_results, min_value=1)

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
                haystack_parts = [a.id or "", a.name or "", a.description or "", a.type or ""]
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

            if len(results) >= effective_limit:
                return

    if space_id:
        await scan_space(space_id)
    else:
        spaces = await client.list_spaces()
        for s in spaces:
            await scan_space(s.id)
            if len(results) >= effective_limit:
                break

    return {
        "space_id": space_id,
        "query": query,
        "limit": effective_limit,
        "requested_limit": requested_limit,
        "cap_limit": cfg.max_search_results,
        "cap_applied": bool(cap_applied),
        "results": results,
        "stats": {"spaces_scanned": spaces_scanned, "assets_scanned": assets_scanned},
    }


async def space_summary(space_id: str, max_assets: int = 50) -> Dict[str, Any]:
    client = _make_client()
    assets = await client.list_space_assets(space_id=space_id)

    type_counts: Dict[str, int] = {}
    for a in assets:
        t = a.type or "<unknown>"
        type_counts[t] = type_counts.get(t, 0) + 1

    sample_assets: List[Dict[str, Any]] = []
    for a in assets[:max_assets]:
        sample_assets.append({"id": a.id, "name": a.name, "type": a.type, "description": a.description})

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
            qr = await client.preview_asset_data(space_id=space_id, asset_name=a.id, top=1)
        except RuntimeError:
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
                qr = await client.preview_asset_data(space_id=sid, asset_name=a.id, top=1)
            except RuntimeError:
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
    cfg = DatasphereConfig.from_env()
    requested_top = top
    effective_top, cap_applied = _cap_int(top, cfg.max_rows_profile, min_value=1)

    client = _make_client()
    qr = await client.preview_asset_data(
        space_id=space_id,
        asset_name=asset_name,
        top=effective_top,
        select=[column_name],
    )

    if not qr.columns:
        raise RuntimeError(
            f"Preview for asset '{asset_name}' in space '{space_id}' returned no columns."
        )

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
    ordered_types = sorted(type_counts.keys(), key=lambda t: type_counts[t], reverse=True)

    numeric_summary: Optional[Dict[str, float]] = None
    numeric_like: List[float] = []

    for v in non_null_values:
        if isinstance(v, (int, float)):
            numeric_like.append(float(v))
        else:
            try:
                numeric_like.append(float(str(v)))
            except Exception:
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
            return numeric_like_sorted[lower] + (numeric_like_sorted[upper] - numeric_like_sorted[lower]) * frac

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
            outlier_count = sum(1 for x in numeric_like_sorted if x < lower_fence or x > upper_fence)

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

    categorical_summary: Optional[Dict[str, Any]] = None
    if non_null_values:
        freq: Dict[Any, int] = {}
        for v in non_null_values:
            freq[v] = freq.get(v, 0) + 1

        unique_values = len(freq)
        non_null_count = len(non_null_values)

        if unique_values <= 50 or unique_values <= max(1, non_null_count // 2):
            sorted_items = sorted(freq.items(), key=lambda item: (-item[1], str(item[0])))
            top_values = []
            for value, count_v in sorted_items[:20]:
                frac = count_v / non_null_count if non_null_count else 0.0
                top_values.append({"value": value, "count": count_v, "fraction": frac})

            concentration = top_values[0]["fraction"] if top_values else None

            categorical_summary = {
                "total_sampled": non_null_count,
                "unique_values": unique_values,
                "top_values": top_values,
                "concentration": concentration,
            }

    role_hint: Optional[str] = None
    non_null_count = len(non_null_values)
    distinct_non_null = len(set(non_null_values)) if non_null_values else 0
    is_numeric = bool(numeric_like)

    name_lower = column_name.lower()

    if non_null_count > 0:
        if any(token in name_lower for token in ("id", "_id", "key", "_key")) and distinct_non_null >= max(
            1, int(0.9 * non_null_count)
        ):
            role_hint = "id"
        elif is_numeric:
            if distinct_non_null > max(5, int(0.5 * non_null_count)):
                role_hint = "measure"
        else:
            if distinct_non_null <= max(50, int(0.7 * non_null_count)):
                role_hint = "dimension"

    meta = {
        "space_id": space_id,
        "asset_name": asset_name,
        "column_name": column_name,
        "sample_rows": total,
        "truncated": qr.truncated,
        "requested_top": requested_top,
        "effective_top": effective_top,
        "cap_top": cfg.max_rows_profile,
        "cap_applied": bool(cap_applied),
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
# Diagnostics & identity helpers
# ---------------------------------------------------------------------------


def _collect_tenant_info() -> Dict[str, Any]:
    """Redacted snapshot of tenant / OAuth configuration from env."""
    cfg = DatasphereConfig.from_env()

    tenant_url = cfg.tenant_url
    token_url = cfg.oauth_token_url

    # Support both names for backwards compatibility in diagnostics.
    client_id = os.getenv("DATASPHERE_CLIENT_ID") or os.getenv("DATASPHERE_OAUTH_CLIENT_ID")
    client_secret = os.getenv("DATASPHERE_CLIENT_SECRET") or os.getenv("DATASPHERE_OAUTH_CLIENT_SECRET")

    host = None
    region = None
    if tenant_url:
        try:
            parsed = urlparse(tenant_url)
            host = parsed.hostname or tenant_url
        except Exception:
            host = tenant_url

        if host:
            parts = host.split(".")
            for part in parts:
                if part[:2] in {"eu", "us", "ap", "sa", "jp", "ca", "au"} and any(ch.isdigit() for ch in part):
                    region = part
                    break

    return {
        "tenant_url": tenant_url,
        "host": host,
        "region_hint": region,
        "mock_mode": bool(cfg.mock_mode),
        "verify_tls": bool(cfg.verify_tls),
        "oauth": {
            "token_url_configured": bool(token_url),
            "client_id_configured": bool(client_id),
            "client_secret_configured": bool(client_secret),
        },
        "limits": {
            "max_rows_preview": cfg.max_rows_preview,
            "max_rows_query": cfg.max_rows_query,
            "max_rows_profile": cfg.max_rows_profile,
            "max_search_results": cfg.max_search_results,
        },
        "cache_config": {
            "ttl_seconds": cfg.cache_ttl_seconds,
            "max_entries": cfg.cache_max_entries,
        },
    }


async def get_tenant_info() -> Dict[str, Any]:
    return _collect_tenant_info()


async def get_current_user() -> Dict[str, Any]:
    info = _collect_tenant_info()
    mock_mode = info["mock_mode"]

    if mock_mode:
        user = {
            "user_known": True,
            "user_id": "MOCK_TECHNICAL_USER",
            "display_name": "Mock Datasphere technical user",
            "source": "mock-mode",
        }
    else:
        user = {
            "user_known": False,
            "message": (
                "The Datasphere MCP server is using client-credentials OAuth "
                "for a technical user. Detailed user identity is not exposed."
            ),
            "source": "config-only",
        }

    return {"mock_mode": mock_mode, "tenant_host": info.get("host"), "user": user}


async def diagnostics() -> Dict[str, Any]:
    started = time.time()
    cfg = DatasphereConfig.from_env()
    config_info = _collect_tenant_info()

    cache = _get_cache(cfg)
    cache.purge_expired()

    checks: List[Dict[str, Any]] = []
    overall_ok = True

    # Client init
    t0 = time.time()
    try:
        client = _make_client()
        checks.append(
            {"name": "client_init", "ok": True, "error": None, "elapsed_ms": int((time.time() - t0) * 1000)}
        )
    except Exception as exc:  # pragma: no cover
        overall_ok = False
        checks.append(
            {
                "name": "client_init",
                "ok": False,
                "error": _make_error("CONFIG_ERROR", str(exc)),
                "elapsed_ms": int((time.time() - t0) * 1000),
            }
        )
        elapsed_ms = int((time.time() - started) * 1000)
        return {
            "ok": False,
            "mock_mode": config_info["mock_mode"],
            "config": config_info,
            "checks": checks,
            "meta": {
                "elapsed_ms": elapsed_ms,
                "cache": cache.stats(),
                "plugins": {
                    "configured": plugin_registry.get_configured_plugins(),
                    "plugins": plugin_registry.get_plugin_status(),
                },
            },
        }

    # Ping
    t0 = time.time()
    try:
        ok_ping = await client.ping()
        if ok_ping:
            checks.append({"name": "ping", "ok": True, "error": None, "elapsed_ms": int((time.time() - t0) * 1000)})
        else:
            overall_ok = False
            checks.append(
                {
                    "name": "ping",
                    "ok": False,
                    "error": _make_error("BACKEND_ERROR", "Ping returned a falsy result."),
                    "elapsed_ms": int((time.time() - t0) * 1000),
                }
            )
    except Exception as exc:
        overall_ok = False
        checks.append(
            {
                "name": "ping",
                "ok": False,
                "error": _make_error("BACKEND_ERROR", str(exc)),
                "elapsed_ms": int((time.time() - t0) * 1000),
            }
        )

    # List spaces
    t0 = time.time()
    try:
        spaces = await client.list_spaces()
        checks.append(
            {
                "name": "list_spaces",
                "ok": True,
                "count": len(spaces),
                "error": None,
                "elapsed_ms": int((time.time() - t0) * 1000),
            }
        )
    except Exception as exc:
        overall_ok = False
        checks.append(
            {
                "name": "list_spaces",
                "ok": False,
                "error": _make_error("BACKEND_ERROR", str(exc)),
                "elapsed_ms": int((time.time() - t0) * 1000),
            }
        )

    elapsed_ms = int((time.time() - started) * 1000)

    plugin_status = plugin_registry.get_plugin_status()
    plugins_info = {
        "configured": plugin_registry.get_configured_plugins(),
        "loaded": sum(1 for p in plugin_status if p.get("ok")),
        "failed": sum(1 for p in plugin_status if not p.get("ok")),
        "plugins": plugin_status,
    }

    return {
        "ok": overall_ok,
        "mock_mode": config_info["mock_mode"],
        "config": config_info,
        "checks": checks,
        "meta": {
            "elapsed_ms": elapsed_ms,
            "cache": cache.stats(),
            "plugins": plugins_info,
        },
    }


# ---------------------------------------------------------------------------
# MCP tool registration
# ---------------------------------------------------------------------------


def register_tools(server: Any) -> None:
    """Register MCP tools on an MCP Server-like instance."""
    if server is None or not hasattr(server, "tool"):
        raise ValueError(
            "register_tools(server) expects an MCP Server-like object that exposes a .tool() decorator."
        )

    @server.tool(name="datasphere_ping", description="Basic health check for the SAP Datasphere MCP server.")
    async def mcp_ping() -> Dict[str, Any]:
        return await ping()

    @server.tool(name="datasphere_list_spaces", description="List SAP Datasphere spaces visible to this OAuth client.")
    async def mcp_list_spaces() -> Dict[str, Any]:
        return await list_spaces()

    @server.tool(name="datasphere_list_assets", description="List catalog assets in a given SAP Datasphere space.")
    async def mcp_list_assets(space_id: str) -> Dict[str, Any]:
        return await list_assets(space_id=space_id)

    @server.tool(name="datasphere_preview_asset", description="Preview a small set of rows from a Datasphere asset.")
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

    @server.tool(
        name="datasphere_describe_asset_schema",
        description="Infer column-oriented schema for a Datasphere asset from a small preview sample.",
    )
    async def mcp_describe_asset_schema(space_id: str, asset_name: str, top: int = 20) -> Dict[str, Any]:
        return await describe_asset_schema(space_id=space_id, asset_name=asset_name, top=top)

    @server.tool(
        name="datasphere_query_relational",
        description="Run a relational query (select / filter / order / paging) against a Datasphere asset.",
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

    @server.tool(
        name="datasphere_get_asset_metadata",
        description="Get catalog metadata for a Datasphere asset, including labels, type and exposure via APIs.",
    )
    async def mcp_get_asset_metadata(space_id: str, asset_name: str) -> Dict[str, Any]:
        return await get_asset_metadata(space_id=space_id, asset_name=asset_name)

    @server.tool(
        name="datasphere_list_columns",
        description="List columns of a Datasphere asset using relational metadata when available (with fallback).",
    )
    async def mcp_list_columns(space_id: str, asset_name: str, max_columns: int = 200) -> Dict[str, Any]:
        return await list_columns(space_id=space_id, asset_name=asset_name, max_columns=max_columns)

    @server.tool(
        name="datasphere_search_assets",
        description="Search for assets by partial name / id / description / type, optionally restricted to a space.",
    )
    async def mcp_search_assets(
        space_id: Optional[str] = None,
        query: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        return await search_assets(space_id=space_id, query=query, limit=limit)

    @server.tool(
        name="datasphere_space_summary",
        description="Summarise assets in a space (counts by type plus a small sample list).",
    )
    async def mcp_space_summary(space_id: str, max_assets: int = 50) -> Dict[str, Any]:
        return await space_summary(space_id=space_id, max_assets=max_assets)

    @server.tool(
        name="datasphere_find_assets_with_column",
        description="Find assets in a space that expose a given column name (case-insensitive, exact match).",
    )
    async def mcp_find_assets_with_column(space_id: str, column_name: str, max_assets: int = 50) -> Dict[str, Any]:
        return await find_assets_with_column(space_id=space_id, column_name=column_name, max_assets=max_assets)

    @server.tool(
        name="datasphere_find_assets_by_column",
        description="Search across one or many spaces for assets that expose a given column name.",
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

    @server.tool(
        name="datasphere_profile_column",
        description="Profile a single column in an asset using a preview sample (numeric & categorical stats).",
    )
    async def mcp_profile_column(
        space_id: str,
        asset_name: str,
        column_name: str,
        top: int = 100,
    ) -> Dict[str, Any]:
        return await profile_column(space_id=space_id, asset_name=asset_name, column_name=column_name, top=top)

    @server.tool(
        name="datasphere_diagnostics",
        description="Run high-level health checks against the MCP server and Datasphere tenant.",
    )
    async def mcp_diagnostics() -> Dict[str, Any]:
        return await diagnostics()

    @server.tool(
        name="datasphere_get_tenant_info",
        description="Return high-level, redacted tenant configuration info (no secrets).",
    )
    async def mcp_get_tenant_info() -> Dict[str, Any]:
        return await get_tenant_info()

    @server.tool(
        name="datasphere_get_current_user",
        description="Describe the current Datasphere identity / technical user without exposing secrets.",
    )
    async def mcp_get_current_user() -> Dict[str, Any]:
        return await get_current_user()
