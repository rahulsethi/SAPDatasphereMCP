# demo_mcp_list_assets.py
# Version: v1
#
# Demo: call the MCP-style list_assets task for a given space.
#
# Usage (PowerShell):
#
#   . .\set-datasphere-env.ps1
#   $env:DATASPHERE_TEST_SPACE = "BW2DS_SPHERESIGHT"   # or GENAI, etc.
#   python demo_mcp_list_assets.py

import asyncio
import os
from typing import Any, Dict, List

from sap_datasphere_mcp.tools import tasks


TEST_SPACE = os.environ.get("DATASPHERE_TEST_SPACE", "BW2DS_SPHERESIGHT")


async def main() -> None:
    print("Calling MCP task: list_assets()")
    print(f"Space id: {TEST_SPACE}")
    print()

    result: Dict[str, Any] = await tasks.list_assets(TEST_SPACE)
    assets: List[Dict[str, Any]] = result.get("assets", [])

    print(f"Assets returned: {len(assets)}")

    if not assets:
        print("No assets found in this space (or access is restricted).")
        return

    for a in assets[:20]:  # just show the first 20 to keep output readable
        aid = a.get("id")
        name = a.get("name")
        atype = a.get("type")
        desc = a.get("description")
        print(f"- {name} (id={aid}, type={atype})  desc={desc!r}")


if __name__ == "__main__":
    asyncio.run(main())
