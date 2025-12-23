# SAP Datasphere MCP Server
# File: config.py
# Version: v2

"""Configuration loading for the SAP Datasphere MCP Server."""

from __future__ import annotations

from dataclasses import dataclass
import os


def _parse_bool_env(name: str, default: bool = False) -> bool:
    """Parse a boolean-like environment variable.

    Accepts 1/0, true/false, yes/no, on/off (case-insensitive).
    """
    val = os.getenv(name)
    if val is None:
        return default
    return str(val).strip().lower() in {"1", "true", "yes", "on"}


def _parse_int_env(
    name: str,
    default: int,
    min_value: int | None = None,
    max_value: int | None = None,
) -> int:
    """Parse an int environment variable with clamping and safe fallback."""
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        value = int(default)
    else:
        try:
            value = int(str(raw).strip())
        except ValueError:
            value = int(default)

    if min_value is not None and value < min_value:
        value = min_value
    if max_value is not None and value > max_value:
        value = max_value

    return value


@dataclass
class DatasphereConfig:
    """Configuration values required to talk to SAP Datasphere.

    v0.3 additions:
    - TLS verification toggle
    - hard caps for row-returning tools
    - metadata TTL cache settings
    """

    tenant_url: str | None
    oauth_token_url: str | None
    client_id: str | None
    client_secret: str | None
    mock_mode: bool

    # v0.3+ hardening
    verify_tls: bool = True
    max_rows_preview: int = 200
    max_rows_query: int = 500
    max_rows_profile: int = 500
    max_search_results: int = 200

    # v0.3+ caching (metadata-focused)
    cache_ttl_seconds: int = 60
    cache_max_entries: int = 128

    @classmethod
    def from_env(cls) -> "DatasphereConfig":
        """Create configuration from environment variables."""
        tenant_url = os.getenv("DATASPHERE_TENANT_URL")
        oauth_token_url = os.getenv("DATASPHERE_OAUTH_TOKEN_URL")
        client_id = os.getenv("DATASPHERE_CLIENT_ID")
        client_secret = os.getenv("DATASPHERE_CLIENT_SECRET")

        mock_mode = _parse_bool_env("DATASPHERE_MOCK_MODE", default=False)
        verify_tls = _parse_bool_env("DATASPHERE_VERIFY_TLS", default=True)

        # Hard caps (tool guardrails)
        max_rows_preview = _parse_int_env(
            "DATASPHERE_MAX_ROWS_PREVIEW", default=200, min_value=1, max_value=10000
        )
        max_rows_query = _parse_int_env(
            "DATASPHERE_MAX_ROWS_QUERY", default=500, min_value=1, max_value=100000
        )
        max_rows_profile = _parse_int_env(
            "DATASPHERE_MAX_ROWS_PROFILE", default=500, min_value=1, max_value=10000
        )
        max_search_results = _parse_int_env(
            "DATASPHERE_MAX_SEARCH_RESULTS", default=200, min_value=1, max_value=10000
        )

        # Cache settings
        cache_ttl_seconds = _parse_int_env(
            "DATASPHERE_CACHE_TTL_SECONDS", default=60, min_value=0, max_value=86400
        )
        cache_max_entries = _parse_int_env(
            "DATASPHERE_CACHE_MAX_ENTRIES", default=128, min_value=0, max_value=10000
        )

        return cls(
            tenant_url=tenant_url,
            oauth_token_url=oauth_token_url,
            client_id=client_id,
            client_secret=client_secret,
            mock_mode=mock_mode,
            verify_tls=verify_tls,
            max_rows_preview=max_rows_preview,
            max_rows_query=max_rows_query,
            max_rows_profile=max_rows_profile,
            max_search_results=max_search_results,
            cache_ttl_seconds=cache_ttl_seconds,
            cache_max_entries=cache_max_entries,
        )
