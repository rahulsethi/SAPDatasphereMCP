# demo_mcp_profile_column.py
# Version: v1

r"""
Quick demo for the datasphere_profile_column() MCP task.

Usage (PowerShell):

  . .\set-datasphere-env.ps1
  $env:DATASPHERE_TEST_SPACE   = "BW2DS_SPHERESIGHT"
  $env:DATASPHERE_TEST_ASSET   = "EMP_View_Test"
  $env:DATASPHERE_TEST_COLUMN  = "SALARY"
  $env:DATASPHERE_TEST_TOP     = "100"
  python demo_mcp_profile_column.py
"""

import asyncio
import os

from sap_datasphere_mcp.tools.tasks import profile_column


SPACE = os.environ.get("DATASPHERE_TEST_SPACE", "BW2DS_SPHERESIGHT")
ASSET = os.environ.get("DATASPHERE_TEST_ASSET", "EMP_View_Test")
COLUMN = os.environ.get("DATASPHERE_TEST_COLUMN", "SALARY")
TOP = int(os.environ.get("DATASPHERE_TEST_TOP", "100"))


async def main() -> None:
    print("Calling MCP task: profile_column()")
    print(f"Space id:   {SPACE}")
    print(f"Asset name: {ASSET}")
    print(f"Column:     {COLUMN}")
    print(f"Top rows:   {TOP}")
    print()

    result = await profile_column(
        space_id=SPACE,
        asset_name=ASSET,
        column_name=COLUMN,
        top=TOP,
    )

    meta = result.get("meta", {})
    print("Sample rows :", meta.get("sample_rows"))
    print("Truncated   :", meta.get("truncated"))
    print("Types       :", result.get("types"))
    print("Total       :", result.get("total_count"))
    print("Nulls       :", result.get("null_count"))
    print("Distinct    :", result.get("distinct_sampled"))
    print()

    if result.get("numeric_summary"):
        ns = result["numeric_summary"]
        print("Numeric summary (sample):")
        print("  min :", ns.get("min"))
        print("  max :", ns.get("max"))
        print("  mean:", ns.get("mean"))
        print()

    print("Example values (sample):")
    print(result.get("example_values"))


if __name__ == "__main__":
    asyncio.run(main())
