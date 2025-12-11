# demo_mcp_query_relational.py
# Version: v1

r"""
Demo: call the MCP task `query_relational` to run a richer query
against a Datasphere asset.

Usage (PowerShell):

  . .\set-datasphere-env.ps1

  # Defaults (BW2DS_SPHERESIGHT / EMP_View_Test, top 10)
  python demo_mcp_query_relational.py

  # With filter and order by:
  $env:DATASPHERE_TEST_SPACE   = "BW2DS_SPHERESIGHT"
  $env:DATASPHERE_TEST_ASSET   = "EMP_View_Test"
  $env:DATASPHERE_TEST_TOP     = "5"
  $env:DATASPHERE_TEST_SKIP    = "0"
  $env:DATASPHERE_TEST_FILTER  = "SALARY gt 100"
  $env:DATASPHERE_TEST_ORDERBY = "HIRE_DATE desc"
  $env:DATASPHERE_TEST_SELECT  = "EMP_ID,FIRST_NAME,LAST_NAME,SALARY"

  python demo_mcp_query_relational.py
"""

from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, List, Optional

from sap_datasphere_mcp.tools.tasks import query_relational


# Read settings from environment, with sensible defaults
SPACE = os.environ.get("DATASPHERE_TEST_SPACE", "BW2DS_SPHERESIGHT")
ASSET = os.environ.get("DATASPHERE_TEST_ASSET", "EMP_View_Test")

TOP = int(os.environ.get("DATASPHERE_TEST_TOP", "10"))
SKIP = int(os.environ.get("DATASPHERE_TEST_SKIP", "0"))

FILTER_EXPR = os.environ.get("DATASPHERE_TEST_FILTER") or None
ORDER_BY = os.environ.get("DATASPHERE_TEST_ORDERBY") or None

_select_raw = os.environ.get("DATASPHERE_TEST_SELECT")
if _select_raw:
    SELECT: Optional[List[str]] = [
        part.strip()
        for part in _select_raw.split(",")
        if part.strip()
    ]
else:
    SELECT = None


async def main() -> None:
    print("Calling MCP task: query_relational()")
    print(f"Space id:    {SPACE}")
    print(f"Asset name:  {ASSET}")
    print(f"Top rows:    {TOP}")
    print(f"Skip rows:   {SKIP}")
    print(f"Filter:      {FILTER_EXPR!r}")
    print(f"Order by:    {ORDER_BY!r}")
    print(f"Select cols: {SELECT!r}")

    result: Dict[str, Any] = await query_relational(
        space_id=SPACE,
        asset_name=ASSET,
        select=SELECT,
        filter_expr=FILTER_EXPR,
        order_by=ORDER_BY,
        top=TOP,
        skip=SKIP,
    )

    columns: List[str] = result.get("columns", []) or []
    rows: List[List[Any]] = result.get("rows", []) or []
    truncated: bool = bool(result.get("truncated", False))
    meta: Dict[str, Any] = result.get("meta", {}) or {}

    print("\nColumns:", columns)
    print("Rows returned:", len(rows))
    print("Truncated:", truncated)
    print("Meta:", meta)

    if not rows:
        print("\nNo rows returned – check your filter/space/asset.")
        return

    print("\nSample rows:")
    for i, row in enumerate(rows[:TOP], start=1):
        print(f"  Row {i}:", row)


if __name__ == "__main__":
    asyncio.run(main())
