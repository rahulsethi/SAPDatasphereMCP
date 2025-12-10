# test_list_spaces.py  v1
"""
Quick smoke test: call SAP Datasphere Catalog API and list spaces.
Run with the virtualenv active and env vars set:
  python test_list_spaces.py
"""

import asyncio
import os

import httpx
from sap_datasphere_mcp.config import DatasphereConfig
from sap_datasphere_mcp.auth import OAuthClient


async def main() -> None:
    # Load config from environment (what we already tested)
    cfg = DatasphereConfig.from_env()
    oauth = OAuthClient(config=cfg)

    token = await oauth.get_access_token()
    print("Got access token of length:", len(token))

    # Catalog API endpoint to list spaces
    # Example from SAP docs / community:
    #   https://<tenant>/api/v1/dwc/catalog/spaces
    base_url = cfg.tenant_url.rstrip("/")
    url = f"{base_url}/api/v1/dwc/catalog/spaces"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, headers=headers)

    print("HTTP status:", resp.status_code)
    if resp.status_code != 200:
        print("Response text:", resp.text[:500])
        return

    data = resp.json()
    # Print a small summary so we don’t dump a huge blob
    if isinstance(data, dict) and "value" in data and isinstance(data["value"], list):
        spaces = data["value"]
        print(f"Spaces returned: {len(spaces)}")
        for s in spaces[:5]:
            print("-", s.get("name") or s.get("id") or s)
    else:
        print("Unexpected JSON structure:")
        print(data)


if __name__ == "__main__":
    asyncio.run(main())
