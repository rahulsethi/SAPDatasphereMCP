# SAP Datasphere MCP Server
# File: auth.py
# Version: v2

"""OAuth2 client for obtaining access tokens for SAP Datasphere."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional
import base64

import httpx

from .config import DatasphereConfig


@dataclass
class OAuthClient:
    """Simple OAuth2 client using the client-credentials flow.

    This implementation follows SAP's recommendation for Technical User
    OAuth clients in SAP Datasphere: credentials are sent via HTTP Basic
    authentication and the request body only contains grant_type.
    """

    config: DatasphereConfig
    _cached_token: Optional[str] = None

    async def get_access_token(self) -> str:
        """Return a valid access token.

        The token is cached in-memory until the process restarts.
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
                "Set DATASPHERE_OAUTH_TOKEN_URL, DATASPHERE_CLIENT_ID "
                "and DATASPHERE_CLIENT_SECRET."
            )

        # Build HTTP Basic Authorization header: base64(client_id:client_secret)
        raw_credentials = f"{self.config.client_id}:{self.config.client_secret}"
        basic_token = base64.b64encode(raw_credentials.encode("utf-8")).decode("ascii")

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {basic_token}",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.config.oauth_token_url,
                data={"grant_type": "client_credentials"},
                headers=headers,
            )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            # Wrap with a clearer message for humans and agents
            status = exc.response.status_code
            body_preview = exc.response.text[:500]
            raise RuntimeError(
                f"Failed to obtain access token from '{self.config.oauth_token_url}' "
                f"(HTTP {status}). Check DATASPHERE_OAUTH_TOKEN_URL, "
                "DATASPHERE_CLIENT_ID and DATASPHERE_CLIENT_SECRET. "
                f"Response snippet: {body_preview}"
            ) from exc

        data: dict[str, Any] = response.json()
        token = data.get("access_token")
        if not token:
            raise RuntimeError("OAuth token response did not contain 'access_token'")

        self._cached_token = token
        return token

