# SAP Datasphere MCP Server
# File: auth.py
# Version: v1

"""OAuth2 client for obtaining access tokens for SAP Datasphere."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import httpx

from .config import DatasphereConfig


@dataclass
class OAuthClient:
    """Simple OAuth2 client using the client-credentials flow.

    In Phase A this is wired but not yet used by real tools.
    """

    config: DatasphereConfig
    _cached_token: Optional[str] = None

    async def get_access_token(self) -> str:
        """Return a valid access token.

        This will be exercised in later phases when we call real Datasphere APIs.
        """
        if self._cached_token:
            return self._cached_token

        if (
            not self.config.oauth_token_url
            or not self.config.client_id
            or not self.config.client_secret
        ):
            raise RuntimeError(
                "OAuth configuration is incomplete. "
                "Set DATASPHERE_OAUTH_TOKEN_URL, DATASPHERE_CLIENT_ID and DATASPHERE_CLIENT_SECRET."
            )

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.config.oauth_token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.config.client_id,
                    "client_secret": self.config.client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            token = data.get("access_token")
            if not token:
                raise RuntimeError("OAuth token response did not contain access_token")
            self._cached_token = token
            return token
