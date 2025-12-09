# SAP Datasphere MCP Server
# File: config.py
# Version: v1

"""Configuration loading for the SAP Datasphere MCP Server."""

from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass
class DatasphereConfig:
    """Configuration values required to talk to SAP Datasphere.

    For Phase A most fields are optional; they will be used in later phases.
    """

    tenant_url: str | None
    oauth_token_url: str | None
    client_id: str | None
    client_secret: str | None
    mock_mode: bool

    @classmethod
    def from_env(cls) -> "DatasphereConfig":
        """Create configuration from environment variables."""
        tenant_url = os.getenv("DATASPHERE_TENANT_URL")
        oauth_token_url = os.getenv("DATASPHERE_OAUTH_TOKEN_URL")
        client_id = os.getenv("DATASPHERE_CLIENT_ID")
        client_secret = os.getenv("DATASPHERE_CLIENT_SECRET")
        mock_mode = os.getenv("DATASPHERE_MOCK_MODE", "false").lower() == "true"

        return cls(
            tenant_url=tenant_url,
            oauth_token_url=oauth_token_url,
            client_id=client_id,
            client_secret=client_secret,
            mock_mode=mock_mode,
        )
