# demo_mcp_search_assets.py
# Version: v1

r"""
Quick demo for the datasphere_search_assets() MCP task.

Usage (PowerShell):

  . .\set-datasphere-env.ps1
  $env:DATASPHERE_TEST_SPACE  = "BW2DS_SPHERESIGHT"   # optional
  $env:DATASPHERE_TEST_SEARCH = "EMP"
  $env:DATASPHERE_TEST_LIMIT  = "20"
  python demo_mcp_search_assets.py
"""

import asyncio
import os

from sap_datasphere_mcp.tools.tasks import search_assets


SPACE = os.environ.get("DATASPHERE_TEST_SPACE") or None
QUERY = os.environ.get("DATASPHERE_TEST_SEARCH", "EMP")
LIMIT = int(os.environ.get("DATASPHERE_TEST_LIMIT", "20"))


async def main() -> None:
    print("Calling MCP task: search_assets()")
    print(f"Space filter: {SPACE!r}")
    print(f"Query:        {QUERY!r}")
    print(f"Limit:        {LIMIT}")
    print()

    result = await search_assets(space_id=SPACE, query=QUERY, limit=LIMIT)

    stats = result.get("stats", {})
    print("Spaces scanned :", stats.get("spaces_scanned"))
    print("Assets scanned :", stats.get("assets_scanned"))
    print("Matches        :", len(result.get("results", [])))
    print()

    for asset in result.get("results", []):
        print(
            f"- {asset['name']} "
            f"(id={asset['id']}, type={asset.get('type')}, "
            f"space={asset.get('space_id')})"
        )
        if asset.get("description"):
            print(f"    desc: {asset['description']}")
    if not result.get("results"):
        print("No matching assets found.")


if __name__ == "__main__":
    asyncio.run(main())
