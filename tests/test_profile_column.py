# SAP Datasphere MCP Server
# File: tests/test_profile_column.py
# Version: v1
#
# Tests for the datasphere_profile_column helper in tools.tasks.
#
# These tests patch `_make_client` so no real Datasphere APIs are called.
# They focus on numeric stats, categorical profiling and the role_hint.

from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from sap_datasphere_mcp.models import QueryResult
from sap_datasphere_mcp.tools import tasks


def _run(coro):
    """Helper to run async coroutines in plain pytest tests."""
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class _FakeProfileClientNumeric:
    """Fake client that returns numeric data for a measure-like column."""

    async def preview_asset_data(
        self,
        space_id: str,
        asset_name: str,
        top: int = 100,
        select=None,
        filter_expr=None,
        order_by=None,
    ) -> QueryResult:
        # 10 numeric sample values with one clear outlier
        # Sorted: [10,10,20,20,30,30,40,40,50,100]
        rows = [
            [10],
            [10],
            [20],
            [20],
            [30],
            [30],
            [40],
            [40],
            [50],
            [100],
        ]
        return QueryResult(
            columns=["AMOUNT"],
            rows=rows,
            truncated=False,
            meta={"space_id": space_id, "asset_name": asset_name},
        )


class _FakeProfileClientId:
    """Fake client for an ID-like integer column."""

    async def preview_asset_data(
        self,
        space_id: str,
        asset_name: str,
        top: int = 100,
        select=None,
        filter_expr=None,
        order_by=None,
    ) -> QueryResult:
        # 10 distinct IDs
        rows = [[i] for i in range(1, 11)]
        return QueryResult(
            columns=["CUSTOMER_ID"],
            rows=rows,
            truncated=False,
            meta={"space_id": space_id, "asset_name": asset_name},
        )


class _FakeProfileClientDimension:
    """Fake client for a low-cardinality string (dimension-like) column."""

    async def preview_asset_data(
        self,
        space_id: str,
        asset_name: str,
        top: int = 100,
        select=None,
        filter_expr=None,
        order_by=None,
    ) -> QueryResult:
        # Mostly OPEN/CLOSED, a few PENDING
        values = ["OPEN"] * 5 + ["CLOSED"] * 3 + ["PENDING"] * 2
        rows = [[v] for v in values]
        return QueryResult(
            columns=["STATUS"],
            rows=rows,
            truncated=False,
            meta={"space_id": space_id, "asset_name": asset_name},
        )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_profile_column_numeric_stats_and_role_hint(monkeypatch) -> None:
    """Numeric column should expose rich numeric stats and 'measure' role hint."""

    fake_client = _FakeProfileClientNumeric()
    monkeypatch.setattr(tasks, "_make_client", lambda: fake_client)

    result = _run(
        tasks.profile_column(
            space_id="SPACE_NUM",
            asset_name="ASSET_NUM",
            column_name="AMOUNT",
            top=100,
        )
    )

    # Core counters
    assert result["total_count"] == 10
    assert result["null_count"] == 0
    assert result["non_null_count"] == 10
    assert result["distinct_sampled"] == 6

    # Numeric summary should be present with expected fields.
    numeric = result["numeric_summary"]
    assert isinstance(numeric, dict)
    assert numeric["min"] == 10
    assert numeric["max"] == 100
    assert numeric["mean"] == 35  # (10+10+20+20+30+30+40+40+50+100)/10
    assert numeric["p50"] == 30
    assert numeric["p25"] == 20
    assert numeric["p75"] == 40
    assert numeric["iqr"] == 20
    assert numeric["lower_fence"] == -10
    assert numeric["upper_fence"] == 70
    assert numeric["outlier_count"] == 1

    # For a numeric, reasonably high-cardinality column, we expect a measure hint.
    assert result["role_hint"] == "measure"


def test_profile_column_id_role_hint(monkeypatch) -> None:
    """ID-like column should be recognised as 'id' via name and high cardinality."""

    fake_client = _FakeProfileClientId()
    monkeypatch.setattr(tasks, "_make_client", lambda: fake_client)

    result = _run(
        tasks.profile_column(
            space_id="SPACE_ID",
            asset_name="ASSET_ID",
            column_name="CUSTOMER_ID",
            top=100,
        )
    )

    assert result["total_count"] == 10
    assert result["null_count"] == 0
    assert result["non_null_count"] == 10

    # All values are distinct, and the name clearly looks like an ID.
    assert result["role_hint"] == "id"


def test_profile_column_dimension_categorical_profile(monkeypatch) -> None:
    """Low-cardinality string column should expose categorical profile & 'dimension'."""

    fake_client = _FakeProfileClientDimension()
    monkeypatch.setattr(tasks, "_make_client", lambda: fake_client)

    result = _run(
        tasks.profile_column(
            space_id="SPACE_DIM",
            asset_name="ASSET_DIM",
            column_name="STATUS",
            top=100,
        )
    )

    # Numeric summary should be absent for purely string data.
    assert result["numeric_summary"] is None

    categorical = result["categorical_summary"]
    assert isinstance(categorical, dict)
    assert categorical["total_sampled"] == 10
    assert categorical["unique_values"] == 3

    # Top value should be OPEN with highest frequency (5/10).
    top_values = categorical["top_values"]
    assert top_values[0]["value"] == "OPEN"
    assert top_values[0]["count"] == 5
    assert abs(top_values[0]["fraction"] - 0.5) < 1e-9
    assert categorical["concentration"] == top_values[0]["fraction"]

    # Role hint for low-cardinality non-numeric columns should be 'dimension'.
    assert result["role_hint"] == "dimension"
