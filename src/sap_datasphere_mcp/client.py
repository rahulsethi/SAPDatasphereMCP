# SAP Datasphere MCP Server
# File: client.py
# Version: v1

"""High-level client for SAP Datasphere REST APIs.

For Phase A this only defines the interface and a simple health check.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

import httpx  # noqa: F401  # used in later phases

from .auth import OAuthClient
from .config import DatasphereConfig
from .models import Space, Asset, QueryResult


@dataclass
class DatasphereClient:
    """Wrapper around SAP Datasphere catalog and consumption APIs."""

    config: DatasphereConfig
    oauth: OAuthClient

    async def ping(self) -> bool:
        """Lightweight health check.

        Right now this just checks that a tenant URL is configured.
        Later we may call a real Datasphere endpoint.
        """
        return bool(self.config.tenant_url)

    # The following methods are placeholders; they will be implemented later.

    async def list_spaces(self) -> List[Space]:
        """List all accessible spaces. Placeholder for Phase B."""
        raise NotImplementedError("list_spaces will be implemented in Phase B")

    async def list_space_assets(self, space_id: str) -> List[Asset]:
        """List assets within a space. Placeholder for Phase B."""
        raise NotImplementedError("list_space_assets will be implemented in Phase B")

    async def preview_asset_data(
        self,
        space_id: str,
        asset_name: str,
        top: int = 20,
    ) -> QueryResult:
        """Preview data from an asset. Placeholder for Phase C."""
        raise NotImplementedError("preview_asset_data will be implemented in Phase C")

    async def query_relational(
        self,
        space_id: str,
        asset_name: str,
        select: Iterable[str] | None = None,
        filter_expr: str | None = None,
        order_by: str | None = None,
        top: int = 100,
        skip: int = 0,
    ) -> QueryResult:
        """Run a relational query. Placeholder for Phase C."""
        raise NotImplementedError("query_relational will be implemented in Phase C")
