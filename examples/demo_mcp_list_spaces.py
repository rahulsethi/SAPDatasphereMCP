# demo_mcp_list_spaces.py
# Version: v1
#
# Demo: call the MCP-style list_spaces task directly and print results.
#
# Usage (PowerShell):
#
#   . .\set-datasphere-env.ps1
#   python demo_mcp_list_spaces.py

import asyncio
from typing import Any, Dict, List

from sap_datasphere_mcp.tools import tasks


async def main() -> None:
    print("Calling MCP task: list_spaces()")
    result: Dict[str, Any] = await tasks.list_spaces()

    spaces: List[Dict[str, Any]] = result.get("spaces", [])
    print(f"Spaces returned: {len(spaces)}")

    if not spaces:
        print("No spaces returned.")
        return

    for s in spaces:
        sid = s.get("id")
        name = s.get("name")
        desc = s.get("description")
        print(f"- {name} (id={sid})  desc={desc!r}")


if __name__ == "__main__":
    asyncio.run(main())
