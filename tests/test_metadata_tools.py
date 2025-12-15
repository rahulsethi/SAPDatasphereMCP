# SAP Datasphere MCP Server
# File: tests/test_metadata_tools.py
# Version: v1

"""Tests for metadata & discovery helpers in tools.tasks.

These tests deliberately patch `_make_client` so that we never talk to a real
SAP Datasphere tenant. All behaviour is verified against simple fake clients.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from sap_datasphere_mcp.models import Asset, QueryResult, Space
from sap_datasphere_mcp.tools import tasks


def _run(coro):
    """Helper to run async coroutines in plain pytest tests."""
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# datasphere_get_asset_metadata
# ---------------------------------------------------------------------------


class _FakeCatalogClient:
    """Fake client that only implements get_catalog_asset."""

    def __init__(self, payload: Dict[str, Any]):
        self.payload = payload
        self.calls: List[Dict[str, Any]] = []

    async def get_catalog_asset(self, space_id: str, asset_id: str) -> Dict[str, Any]:
        self.calls.append({"space_id": space_id, "asset_id": asset_id})
        return self.payload


def test_get_asset_metadata_summarises_basic_fields(monkeypatch) -> None:
    """get_asset_metadata should expose key summary fields and raw payload."""

    payload = {
        "id": "SALES_VIEW",
        "name": "Sales View",
        "label": "Sales View Label",
        "description": "Test asset for metadata tooling.",
        "type": "VIEW",
        # Only relational URLs -> analytical flags should be False.
        "assetRelationalMetadataUrl": "/catalog/relational/$metadata",
        "assetRelationalDataUrl": "/catalog/relational/data",
    }

    fake_client = _FakeCatalogClient(payload)
    monkeypatch.setattr(tasks, "_make_client", lambda: fake_client)

    result = _run(tasks.get_asset_metadata("SPACE_1", "SALES_VIEW"))

    # Basic identity fields
    assert result["space_id"] == "SPACE_1"
    assert result["asset_id"] == "SALES_VIEW"
    assert result["name"] == "Sales View"
    assert result["label"] == "Sales View Label"
    assert result["description"] == "Test asset for metadata tooling."
    assert result["type"] == "VIEW"

    # Capability flags derived from URLs
    assert result["supports_relational_queries"] is True
    assert result["supports_analytical_queries"] is False

    # Raw payload should be preserved for advanced use.
    assert result["raw"] == payload

    # Sanity-check that the fake client was actually used.
    assert fake_client.calls == [{"space_id": "SPACE_1", "asset_id": "SALES_VIEW"}]


# ---------------------------------------------------------------------------
# datasphere_list_columns
# ---------------------------------------------------------------------------


_RELATIONAL_METADATA_XML = """<?xml version="1.0" encoding="utf-8"?>
<edmx:Edmx xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx">
  <edmx:DataServices>
    <Schema Namespace="Test" xmlns="http://docs.oasis-open.org/odata/ns/edm">
      <EntityType Name="Main">
        <Key>
          <PropertyRef Name="ID" />
        </Key>
        <Property Name="ID" Type="Edm.String" Nullable="false" />
        <Property Name="AMOUNT" Type="Edm.Decimal" Nullable="true" />
      </EntityType>
    </Schema>
  </edmx:DataServices>
</edmx:Edmx>
"""


class _FakeRelationalMetadataClient:
    """Fake client that returns a small EDMX $metadata document."""

    async def get_relational_metadata(self, space_id: str, asset_name: str) -> str:
        # Basic sanity check on arguments so test will fail on regression.
        assert space_id == "SPACE_META"
        assert asset_name == "ASSET_META"
        return _RELATIONAL_METADATA_XML

    async def preview_asset_data(self, *args, **kwargs):
        # If the implementation unexpectedly falls back to preview, fail fast.
        raise AssertionError("preview_asset_data should not be called in this test")


def test_list_columns_prefers_relational_metadata(monkeypatch) -> None:
    """list_columns should use $metadata when it yields columns."""

    fake_client = _FakeRelationalMetadataClient()
    monkeypatch.setattr(tasks, "_make_client", lambda: fake_client)

    result = _run(tasks.list_columns("SPACE_META", "ASSET_META"))

    assert result["space_id"] == "SPACE_META"
    assert result["asset_name"] == "ASSET_META"
    assert result["meta"]["source"] == "relational_metadata"

    column_names = {col["name"] for col in result["columns"]}
    assert {"ID", "AMOUNT"} <= column_names

    # ID should be recognised as a key and non-nullable.
    id_col = next(col for col in result["columns"] if col["name"] == "ID")
    assert id_col["is_key"] is True
    assert id_col["nullable"] is False


class _FakePreviewOnlyClient:
    """Fake client where relational metadata fails, forcing preview fallback."""

    async def get_relational_metadata(self, space_id: str, asset_name: str) -> str:
        raise RuntimeError("No relational metadata available")

    async def preview_asset_data(
        self,
        space_id: str,
        asset_name: str,
        top: int = 1,
        select=None,
        filter_expr=None,
        order_by=None,
    ) -> QueryResult:
        assert top == 1
        # Simple two-column result is enough to infer names.
        return QueryResult(
            columns=["C1", "C2"],
            rows=[[1, "x"], [2, "y"]],
            truncated=False,
            meta={"space_id": space_id, "asset_name": asset_name},
        )


def test_list_columns_falls_back_to_preview(monkeypatch) -> None:
    """When relational metadata fails, list_columns should infer names from preview."""

    fake_client = _FakePreviewOnlyClient()
    monkeypatch.setattr(tasks, "_make_client", lambda: fake_client)

    result = _run(tasks.list_columns("SPACE_PREVIEW", "ASSET_PREVIEW"))

    assert result["meta"]["source"] == "sample_inference"
    assert [c["name"] for c in result["columns"]] == ["C1", "C2"]

    # Fallback columns do not know types / keys.
    assert all(c["type"] is None for c in result["columns"])
    assert all(c["nullable"] is None for c in result["columns"])
    assert all(c["is_key"] is False for c in result["columns"])


# ---------------------------------------------------------------------------
# datasphere_find_assets_by_column
# ---------------------------------------------------------------------------


class _FakeFindAssetsClient:
    """Fake client for cross-space column search."""

    async def list_spaces(self) -> List[Space]:
        return [
            Space(id="SPACE_A", name="Space A"),
            Space(id="SPACE_B", name="Space B"),
        ]

    async def list_space_assets(self, space_id: str) -> List[Asset]:
        if space_id == "SPACE_A":
            return [
                Asset(id="A1", name="Asset A1", space_id="SPACE_A"),
                Asset(id="A2", name="Asset A2", space_id="SPACE_A"),
            ]
        return [
            Asset(id="B1", name="Asset B1", space_id="SPACE_B"),
        ]

    async def preview_asset_data(
        self,
        space_id: str,
        asset_name: str,
        top: int = 1,
        select=None,
        filter_expr=None,
        order_by=None,
    ) -> QueryResult:
        # Only some assets expose TARGET_COL.
        if asset_name in {"A1", "B1"}:
            columns = ["ID", "TARGET_COL"]
        else:
            columns = ["ID", "OTHER"]
        return QueryResult(
            columns=columns,
            rows=[[1, 2]],
            truncated=False,
            meta={"space_id": space_id, "asset_id": asset_name},
        )


def test_find_assets_by_column_across_spaces(monkeypatch) -> None:
    """find_assets_by_column should return matches across multiple spaces."""

    fake_client = _FakeFindAssetsClient()
    monkeypatch.setattr(tasks, "_make_client", lambda: fake_client)

    result = _run(
        tasks.find_assets_by_column(
            column_name="TARGET_COL",
            space_id=None,
            limit=10,
            max_spaces=5,
            max_assets_per_space=5,
        )
    )

    matches = {(r["space_id"], r["asset_id"]) for r in result["results"]}

    # We expect one match per space where TARGET_COL appears.
    assert ("SPACE_A", "A1") in matches
    assert ("SPACE_B", "B1") in matches

    # Sanity-check stats are populated.
    assert result["stats"]["spaces_scanned"] == 2
    assert result["stats"]["assets_scanned"] >= 2
