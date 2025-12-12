# demo_mcp_space_summary.py
# Version: v1

r"""
Quick demo for the datasphere_space_summary() MCP task.

Usage (PowerShell):

  . .\set-datasphere-env.ps1
  $env:DATASPHERE_TEST_SPACE = "BW2DS_SPHERESIGHT"
  python demo_mcp_space_summary.py
"""

import asyncio
import os

from sap_datasphere_mcp.tools.tasks import space_summary


SPACE = os.environ.get("DATASPHERE_TEST_SPACE", "BW2DS_SPHERESIGHT")
MAX_ASSETS = int(os.environ.get("DATASPHERE_TEST_MAX_ASSETS", "20"))


async def main() -> None:
    print("Calling MCP task: space_summary()")
    print(f"Space id:    {SPACE}")
    print(f"Max assets:  {MAX_ASSETS}")
    print()

    result = await space_summary(space_id=SPACE, max_assets=MAX_ASSETS)

    print("Total assets :", result.get("total_assets"))
    print("Asset types  :")
    for t, count in (result.get("asset_types") or {}).items():
        print(f"  - {t}: {count}")
    print()

    print("Sample assets:")
    for a in result.get("sample_assets", []):
        print(f"- {a['name']} (id={a['id']}, type={a.get('type')})")
        if a.get("description"):
            print(f"    desc: {a['description']}")


if __name__ == "__main__":
    asyncio.run(main())
