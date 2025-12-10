# test_preview_asset.py
# Version: v3

r"""
Quick sanity check: fetch a few rows from a Datasphere asset
using DatasphereClient.preview_asset_data().

Run this from a shell where you've already done:
  . .\set-datasphere-env.ps1

Optionally override the defaults with:
  $env:DATASPHERE_TEST_SPACE = "GENAI"
  $env:DATASPHERE_TEST_ASSET = "ZPC_MULTI"
  $env:DATASPHERE_TEST_TOP   = "5"
"""

import asyncio
import os

from sap_datasphere_mcp.config import DatasphereConfig
from sap_datasphere_mcp.auth import OAuthClient
from sap_datasphere_mcp.client import DatasphereClient


TEST_SPACE = os.environ.get("DATASPHERE_TEST_SPACE", "GENAI")
TEST_ASSET = os.environ.get("DATASPHERE_TEST_ASSET", "ZPC_MULTI")
TEST_TOP = int(os.environ.get("DATASPHERE_TEST_TOP", "5"))


async def main() -> None:
    cfg = DatasphereConfig.from_env()
    oauth = OAuthClient(config=cfg)
    client = DatasphereClient(config=cfg, oauth=oauth)

    print(f"Space: {TEST_SPACE}  Asset: {TEST_ASSET}  Top: {TEST_TOP}")

    try:
        result = await client.preview_asset_data(
            space_id=TEST_SPACE,
            asset_name=TEST_ASSET,
            top=TEST_TOP,
        )
    except RuntimeError as exc:
        # Friendlier error for assets that are not consumable (404 etc.)
        print("Error while previewing data:")
        print(str(exc))
        return

    print("Columns:", result.columns)
    print("Rows returned:", len(result.rows))

    if not result.rows:
        print(
            "No rows returned – the asset may be empty or not provide any rows "
            "for the current query (e.g. fact view with no data)."
        )
        return

    for i, row in enumerate(result.rows[:TEST_TOP], start=1):
        print(f"Row {i}:", row)


if __name__ == "__main__":
    asyncio.run(main())
