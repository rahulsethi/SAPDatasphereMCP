# SAP Datasphere MCP Server
# File: auth.py
# Version: v3

"""OAuth2 client for obtaining access tokens for SAP Datasphere.

Client-credentials flow (Technical User):
- Sends credentials via HTTP Basic auth (SAP recommended).
- Caches token in-memory until shortly before expiry.
- Respects DATASPHERE_VERIFY_TLS via DatasphereConfig.verify_tls.
- Supports DATASPHERE_MOCK_MODE via DatasphereConfig.mock_mode.
"""

from __future__ import annotations

import asyncio
import base64
import os
import time
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx

from .config import DatasphereConfig


@dataclass
class OAuthClient:
    """OAuth2 client using the client-credentials flow."""

    config: DatasphereConfig

    # Cached token state (in-memory)
    _cached_token: Optional[str] = None
    _expires_at: Optional[float] = None  # epoch seconds

    # Prevent token stampedes under concurrency
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False, repr=False)

    # Refresh token slightly before expiry
    _expiry_leeway_seconds: int = field(default=30, init=False, repr=False)

    def invalidate(self) -> None:
        """Forget cached token so next request re-authenticates."""
        self._cached_token = None
        self._expires_at = None

    def _token_valid(self) -> bool:
        if not self._cached_token or not self._expires_at:
            return False
        return time.time() < (self._expires_at - float(self._expiry_leeway_seconds))

    async def get_access_token(self) -> str:
        """Return a valid access token (cached until near-expiry)."""
        if self.config.mock_mode:
            return "MOCK_ACCESS_TOKEN"

        if self._token_valid():
            return self._cached_token  # type: ignore[return-value]

        async with self._lock:
            # Re-check under lock
            if self._token_valid():
                return self._cached_token  # type: ignore[return-value]

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
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {basic_token}",
            }

            data: dict[str, Any] = {"grant_type": "client_credentials"}

            # Optional scope support (safe to ignore if unused)
            scope = os.getenv("DATASPHERE_OAUTH_SCOPE")
            if scope:
                data["scope"] = scope

            async with httpx.AsyncClient(timeout=30.0, verify=self.config.verify_tls) as client:
                try:
                    response = await client.post(
                        self.config.oauth_token_url,
                        data=data,
                        headers=headers,
                    )
                except httpx.RequestError as exc:
                    raise RuntimeError(
                        f"Error calling OAuth token endpoint '{self.config.oauth_token_url}': {exc}"
                    ) from exc

                # Some environments expect client credentials in the POST body.
                # Try a fallback only for auth-ish failures.
                if response.status_code in {400, 401}:
                    try:
                        body_fallback = dict(data)
                        body_fallback["client_id"] = self.config.client_id
                        body_fallback["client_secret"] = self.config.client_secret
                        response2 = await client.post(
                            self.config.oauth_token_url,
                            data=body_fallback,
                            headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
                        )
                        if 200 <= response2.status_code < 300:
                            response = response2
                    except httpx.RequestError as exc:
                        raise RuntimeError(
                            f"Error calling OAuth token endpoint '{self.config.oauth_token_url}': {exc}"
                        ) from exc

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                body_preview = (exc.response.text or "")[:500]
                raise RuntimeError(
                    f"Failed to obtain access token from '{self.config.oauth_token_url}' "
                    f"(HTTP {status}). Check DATASPHERE_OAUTH_TOKEN_URL, "
                    "DATASPHERE_CLIENT_ID and DATASPHERE_CLIENT_SECRET. "
                    f"Response snippet: {body_preview}"
                ) from exc

            payload: dict[str, Any] = response.json()
            token = payload.get("access_token")
            if not token:
                raise RuntimeError("OAuth token response did not contain 'access_token'")

            expires_in = payload.get("expires_in")
            try:
                expires_in_s = int(expires_in) if expires_in is not None else 300
            except Exception:
                expires_in_s = 300

            self._cached_token = str(token)
            self._expires_at = time.time() + float(max(1, expires_in_s))
            return self._cached_token
