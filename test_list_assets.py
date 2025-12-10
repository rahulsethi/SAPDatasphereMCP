# test_list_assets.py
# Version: v2

r"""
Quick smoke test: list catalog assets for a space in SAP Datasphere.

Run with virtualenv active and env vars loaded:
  . .\set-datasphere-env.ps1
  python test_list_assets.py
"""

import asyncio

from sap_datasphere_mcp.config import DatasphereConfig
from sap_datasphere_mcp.auth import OAuthClient
from sap_datasphere_mcp.client import DatasphereClient


async def main() -> None:
    cfg = DatasphereConfig.from_env()
    oauth = OAuthClient(config=cfg)
    client = DatasphereClient(config=cfg, oauth=oauth)

    spaces = await client.list_spaces()
    if not spaces:
        print("No spaces returned from catalog; cannot test assets.")
        return

    # For now just pick the first space; you can change to 'GENAI' or others.
    space = spaces[0]
    print(f"Using space: {space.id} ({space.name})")

    assets = await client.list_space_assets(space_id=space.id)
    print("Assets returned:", len(assets))

    for a in assets[:10]:
        print(f"- {a.name} (id={a.id}, type={a.type})")


if __name__ == "__main__":
    asyncio.run(main())
