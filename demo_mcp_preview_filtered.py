# demo_mcp_preview_filtered.py
# Version: v1
#
# Demo: call the MCP-style preview_asset task with a filter expression.
#
# Usage (PowerShell):
#
#   . .\set-datasphere-env.ps1
#   $env:DATASPHERE_TEST_SPACE  = "BW2DS_SPHERESIGHT"
#   $env:DATASPHERE_TEST_ASSET  = "EMP_View_Test"
#   $env:DATASPHERE_TEST_TOP    = "5"
#   $env:DATASPHERE_TEST_FILTER = "SALARY gt 100"
#   python demo_mcp_preview_filtered.py
#
# Adjust DATASPHERE_TEST_FILTER as needed (OData-style syntax).

import asyncio
import os
from typing import Any, Dict

from sap_datasphere_mcp.tools import tasks

TEST_SPACE = os.environ.get("DATASPHERE_TEST_SPACE", "BW2DS_SPHERESIGHT")
TEST_ASSET = os.environ.get("DATASPHERE_TEST_ASSET", "EMP_View_Test")
TEST_TOP = int(os.environ.get("DATASPHERE_TEST_TOP", "5"))
TEST_FILTER = os.environ.get("DATASPHERE_TEST_FILTER", "SALARY gt 100")


async def main() -> None:
    print("Calling MCP task: preview_asset() with filter")
    print(f"Space id:   {TEST_SPACE}")
    print(f"Asset name: {TEST_ASSET}")
    print(f"Top rows:   {TEST_TOP}")
    print(f"Filter:     {TEST_FILTER!r}")
    print()

    result: Dict[str, Any] = await tasks.preview_asset(
        space_id=TEST_SPACE,
        asset_name=TEST_ASSET,
        top=TEST_TOP,
        filter_expr=TEST_FILTER,
    )

    columns = result.get("columns", [])
    rows = result.get("rows", [])
    truncated = result.get("truncated")
    meta = result.get("meta", {})

    print("Columns:", columns)
    print("Rows returned:", len(rows))
    print("Truncated:", truncated)
    print("Meta:", meta)
    print()

    if not rows:
        print("No rows returned – the filter may have excluded all data.")
        return

    print("Sample rows:")
    for i, row in enumerate(rows, start=1):
        print(f"  Row {i}: {row}")


if __name__ == "__main__":
    asyncio.run(main())
