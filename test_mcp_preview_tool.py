# test_mcp_preview_tool.py
# Version: v2
#
# Sanity test for the MCP-layer `preview_asset` tool.
#
# This calls the MCP tool function directly (without an MCP host) to
# ensure the wiring from tools.tasks -> DatasphereClient works end-to-end.
#
# Usage (PowerShell):
#
#   . .\set-datasphere-env.ps1
#
#   $env:DATASPHERE_TEST_SPACE = "BW2DS_SPHERESIGHT"
#   $env:DATASPHERE_TEST_ASSET = "EMP_View_Test"
#   $env:DATASPHERE_TEST_TOP   = "5"
#
#   python test_mcp_preview_tool.py

import asyncio
import os
from typing import Any, Dict, List

# NOTE: tasks.py lives under the "tools" package in this project.
from sap_datasphere_mcp.tools.tasks import preview_asset


TEST_SPACE = os.environ.get("DATASPHERE_TEST_SPACE", "BW2DS_SPHERESIGHT")
TEST_ASSET = os.environ.get("DATASPHERE_TEST_ASSET", "EMP_View_Test")
TEST_TOP = int(os.environ.get("DATASPHERE_TEST_TOP", "5"))


async def main() -> None:
    print("Calling MCP tool preview_asset for:")
    print(f"  space_id  = {TEST_SPACE}")
    print(f"  asset_name= {TEST_ASSET}")
    print(f"  top       = {TEST_TOP}")
    print()

    try:
        result: Dict[str, Any] = await preview_asset(
            space_id=TEST_SPACE,
            asset_name=TEST_ASSET,
            top=TEST_TOP,
        )
    except Exception as exc:  # noqa: BLE001
        print("Error while calling preview_asset MCP tool:")
        print(str(exc))
        return

    columns: List[str] = result.get("columns", [])
    rows: List[List[Any]] = result.get("rows", [])
    truncated: bool = bool(result.get("truncated", False))
    meta: Dict[str, Any] = result.get("meta", {})

    print("Columns:", columns)
    print("Rows returned:", len(rows))
    print("Truncated:", truncated)
    print("Meta:", meta)
    print()

    if not rows:
        print(
            "No rows returned – the asset may be empty or not provide any rows "
            "for the current query."
        )
        return

    print("Sample rows:")
    for i, row in enumerate(rows[:TEST_TOP], start=1):
        print(f"  Row {i}:", row)


if __name__ == "__main__":
    asyncio.run(main())
