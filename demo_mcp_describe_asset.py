# demo_mcp_describe_asset.py
# Version: v1
#
# Demo: call the MCP-style describe_asset_schema task and print column info.
#
# Usage (PowerShell):
#
#   . .\set-datasphere-env.ps1
#   $env:DATASPHERE_TEST_SPACE = "BW2DS_SPHERESIGHT"
#   $env:DATASPHERE_TEST_ASSET = "EMP_View_Test"
#   python demo_mcp_describe_asset.py

import asyncio
import os
from typing import Any, Dict, List

from sap_datasphere_mcp.tools import tasks

TEST_SPACE = os.environ.get("DATASPHERE_TEST_SPACE", "BW2DS_SPHERESIGHT")
TEST_ASSET = os.environ.get("DATASPHERE_TEST_ASSET", "EMP_View_Test")
TEST_TOP = int(os.environ.get("DATASPHERE_TEST_TOP", "5"))


async def main() -> None:
    print("Calling MCP task: describe_asset_schema()")
    print(f"Space id:  {TEST_SPACE}")
    print(f"Asset name:{TEST_ASSET}")
    print(f"Top rows:  {TEST_TOP}")
    print()

    result: Dict[str, Any] = await tasks.describe_asset_schema(
        space_id=TEST_SPACE,
        asset_name=TEST_ASSET,
        top=TEST_TOP,
    )

    print(f"Row count (preview): {result.get('row_count_preview')}")
    print(f"Truncated:           {result.get('truncated')}")
    print()

    columns: List[Dict[str, Any]] = result.get("columns", [])
    print(f"Columns discovered:  {len(columns)}")
    print()

    for col in columns:
        name = col.get("name")
        inferred_types = col.get("inferred_types")
        non_null = col.get("non_null_count")
        total = col.get("total_count")
        examples = col.get("examples", [])

        print(f"- {name}")
        print(f"    types:      {inferred_types}")
        print(f"    non-null:   {non_null} / {total}")
        print(f"    examples:   {examples}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
