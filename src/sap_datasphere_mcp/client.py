# SAP Datasphere MCP Server
# File: client.py
# Version: v13 (1.0)
"""High-level client for SAP Datasphere REST APIs.

Implements:

- list_spaces() via the Catalog API
- list_space_assets() via the Catalog API
- preview_asset_data() via the relational Consumption API
- query_relational() via the relational Consumption API
- query_analytical() via the analytical Consumption API (v0.3+)
- get_catalog_asset() for per-asset catalog metadata
- get_relational_metadata() for relational OData $metadata

Notes on URL variants (v1.0 path migration):

- The modern path is ``/api/v1/datasphere/...`` (Datasphere Wave 2025.19+).
- The legacy ``/api/v1/dwc/...`` path is deprecated; supported by SAP through
  March 2027.
- v1.0 defaults to **modern first, legacy fallback** on 404/405.
- Set ``DATASPHERE_API_PATH_LEGACY=1`` to flip the order for tenants stuck on
  an older wave.

The Catalog moved further under ``/consumption/catalog/`` in the modern
shape; we list both ``/datasphere/catalog`` and ``/datasphere/consumption/catalog``
so we cover tenants on either layout.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

import httpx
from httpx import HTTPStatusError, RequestError

from .auth import OAuthClient
from .config import DatasphereConfig
from .models import Asset, QueryResult, Space


def _legacy_paths_first() -> bool:
    raw = os.environ.get("DATASPHERE_API_PATH_LEGACY", "")
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class DatasphereClient:
    """Wrapper around SAP Datasphere catalog and consumption APIs."""

    config: DatasphereConfig
    oauth: OAuthClient

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _base_url(self) -> str:
        if not self.config.tenant_url:
            raise RuntimeError(
                "DATASPHERE_TENANT_URL is not set. "
                "Please configure it before calling Datasphere APIs."
            )
        return self.config.tenant_url.rstrip("/")

    @property
    def path_mode(self) -> str:
        """Return ``"legacy"`` or ``"modern"`` for diagnostics."""
        return "legacy" if _legacy_paths_first() else "modern"

    def _catalog_prefixes(self) -> List[str]:
        """Return catalog base prefixes in fallback order.

        v1.0 default: modern (``/api/v1/datasphere/...``) first; legacy
        (``/api/v1/dwc/...``) fallback. Flip via ``DATASPHERE_API_PATH_LEGACY=1``.

        Both ``/datasphere/catalog`` and ``/datasphere/consumption/catalog``
        are listed for the modern shape because the Catalog moved further
        under the Consumption tree in Wave 2025.19.
        """
        base = self._base_url()
        modern = [
            f"{base}/api/v1/datasphere/consumption/catalog",
            f"{base}/api/v1/datasphere/catalog",
        ]
        legacy = [f"{base}/api/v1/dwc/catalog"]
        return (legacy + modern) if _legacy_paths_first() else (modern + legacy)

    def _consumption_prefixes(self) -> List[str]:
        """Return consumption base prefixes in fallback order.

        v1.0 default: modern (``/api/v1/datasphere/consumption``) first; legacy
        (``/api/v1/dwc/consumption``) fallback. Flip via
        ``DATASPHERE_API_PATH_LEGACY=1``.
        """
        base = self._base_url()
        modern = f"{base}/api/v1/datasphere/consumption"
        legacy = f"{base}/api/v1/dwc/consumption"
        return [legacy, modern] if _legacy_paths_first() else [modern, legacy]

    async def _get_with_fallback(
        self,
        *,
        urls: List[str],
        headers: Dict[str, str],
        params: Optional[Dict[str, Any]] = None,
        timeout_seconds: float = 60.0,
        allow_top_fallback: bool = False,
    ) -> httpx.Response:
        """GET the first working URL from a list of candidates.

        - Retries without $top on the same URL if server returns the known message.
        - Falls back to the next URL on 404/405 (common for wrong prefix/pattern).
        """
        if not urls:
            raise RuntimeError("No URL candidates provided for Datasphere request.")

        async with httpx.AsyncClient(timeout=timeout_seconds, verify=self.config.verify_tls) as http_client:
            last_http_exc: Optional[HTTPStatusError] = None

            for url in urls:
                try:
                    response = await http_client.get(url, headers=headers, params=params or None)

                    if (
                        allow_top_fallback
                        and response.status_code == 400
                        and "Query option '$top' is not supported" in (response.text or "")
                        and params
                        and "$top" in params
                    ):
                        params2 = dict(params)
                        params2.pop("$top", None)
                        response = await http_client.get(url, headers=headers, params=params2 or None)

                    response.raise_for_status()
                    return response

                except RequestError as exc:
                    raise RuntimeError(f"Error calling Datasphere API at '{url}': {exc}") from exc

                except HTTPStatusError as exc:
                    last_http_exc = exc
                    status = exc.response.status_code if exc.response is not None else None

                    # Only fall back on "likely wrong URL variant" signals.
                    if status in {404, 405}:
                        continue

                    body_preview = (exc.response.text or "")[:500] if exc.response is not None else ""
                    raise RuntimeError(
                        f"Failed to call Datasphere API at '{url}' (HTTP {status}). "
                        f"Response snippet: {body_preview}"
                    ) from exc

            # Exhausted candidates.
            if last_http_exc is not None and last_http_exc.response is not None:
                last_url = str(last_http_exc.response.request.url)
                status = last_http_exc.response.status_code
                body_preview = (last_http_exc.response.text or "")[:500]
                raise RuntimeError(
                    f"Failed to call Datasphere API; tried {len(urls)} URL variants. "
                    f"Last attempt '{last_url}' (HTTP {status}). "
                    f"Response snippet: {body_preview}"
                ) from last_http_exc

            raise RuntimeError(f"Failed to call Datasphere API; tried {len(urls)} URL variants.")

    # ------------------------------------------------------------------
    # Basic health
    # ------------------------------------------------------------------

    async def ping(self) -> bool:
        """Lightweight health check.

        For now this just checks that a tenant URL is configured.
        Later we may call a real Datasphere endpoint.
        """
        return bool(self.config.tenant_url)

    # ------------------------------------------------------------------
    # Catalog: spaces
    # ------------------------------------------------------------------

    async def list_spaces(self) -> List[Space]:
        """List all accessible Datasphere spaces via the catalog API."""
        token = await self.oauth.get_access_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        urls = [f"{prefix}/spaces" for prefix in self._catalog_prefixes()]
        response = await self._get_with_fallback(urls=urls, headers=headers, params=None, timeout_seconds=30.0)

        data = response.json()
        raw_spaces = data.get("value") if isinstance(data, dict) else data

        spaces: List[Space] = []
        if isinstance(raw_spaces, list):
            for item in raw_spaces:
                if not isinstance(item, dict):
                    continue

                space_id = item.get("id") or item.get("technicalName") or item.get("name")
                name = item.get("name") or space_id or ""
                description = item.get("description")

                spaces.append(
                    Space(
                        id=str(space_id),
                        name=str(name),
                        description=description,
                        raw=item,
                    )
                )

        return spaces

    # ------------------------------------------------------------------
    # Catalog: assets
    # ------------------------------------------------------------------

    async def list_space_assets(self, space_id: str) -> List[Asset]:
        """List catalog assets within a given Datasphere space."""
        token = await self.oauth.get_access_token()

        # Single quotes must be escaped for OData key literals.
        key_space_id = space_id.replace("'", "''")

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        urls = [f"{prefix}/spaces('{key_space_id}')/assets" for prefix in self._catalog_prefixes()]
        response = await self._get_with_fallback(urls=urls, headers=headers, params=None, timeout_seconds=30.0)

        data = response.json()
        raw_assets = data.get("value") if isinstance(data, dict) else data

        assets: List[Asset] = []
        if isinstance(raw_assets, list):
            for item in raw_assets:
                if not isinstance(item, dict):
                    continue

                asset_id = item.get("id") or item.get("technicalName") or item.get("name")
                name = item.get("name") or asset_id or ""
                asset_type = item.get("type") or item.get("assetType") or item.get("kind")
                description = item.get("description")

                assets.append(
                    Asset(
                        id=str(asset_id),
                        name=str(name),
                        type=str(asset_type) if asset_type is not None else None,
                        space_id=space_id,
                        description=description,
                        raw=item,
                    )
                )

        return assets

    async def get_catalog_asset(self, space_id: str, asset_id: str) -> Dict[str, Any]:
        """Get catalog metadata for a single asset in a space."""
        token = await self.oauth.get_access_token()

        key_space_id = space_id.replace("'", "''")
        key_asset_id = asset_id.replace("'", "''")

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        urls = [
            f"{prefix}/spaces('{key_space_id}')/assets('{key_asset_id}')"
            for prefix in self._catalog_prefixes()
        ]
        response = await self._get_with_fallback(urls=urls, headers=headers, params=None, timeout_seconds=30.0)

        data = response.json()
        if not isinstance(data, dict):
            raise RuntimeError(
                "Unexpected response when fetching catalog asset "
                f"'{asset_id}' in space '{space_id}': "
                f"expected JSON object, got {type(data).__name__}."
            )

        return data

    # ------------------------------------------------------------------
    # Consumption: preview data (relational API)
    # ------------------------------------------------------------------

    async def preview_asset_data(
        self,
        space_id: str,
        asset_name: str,
        top: int = 20,
        select: Iterable[str] | None = None,
        filter_expr: str | None = None,
        order_by: str | None = None,
    ) -> QueryResult:
        """Fetch a small sample of rows from a Datasphere asset."""
        token = await self.oauth.get_access_token()

        params: Dict[str, Any] = {}
        if top is not None:
            params["$top"] = int(top)
        if select:
            params["$select"] = ",".join(select)
        if filter_expr:
            params["$filter"] = filter_expr
        if order_by:
            params["$orderby"] = order_by

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        urls: List[str] = []
        for prefix in self._consumption_prefixes():
            urls.append(f"{prefix}/relational/{space_id}/{asset_name}/{asset_name}")
            urls.append(f"{prefix}/relational/{space_id}/{asset_name}/{space_id}/{asset_name}/{asset_name}")

        response = await self._get_with_fallback(
            urls=urls,
            headers=headers,
            params=params or None,
            timeout_seconds=60.0,
            allow_top_fallback=True,
        )

        data = response.json()
        raw_rows = data.get("value") if isinstance(data, dict) else data

        rows_dicts: List[Dict[str, Any]] = []
        if isinstance(raw_rows, list):
            rows_dicts = [r for r in raw_rows if isinstance(r, dict)]

        if not rows_dicts:
            return QueryResult(
                columns=[],
                rows=[],
                truncated=False,
                meta={
                    "space_id": space_id,
                    "asset_name": asset_name,
                    "row_count": 0,
                    "top": top,
                },
            )

        columns = list(rows_dicts[0].keys())
        rows = [[row.get(col) for col in columns] for row in rows_dicts]
        truncated = top is not None and len(rows) >= top

        meta = {
            "space_id": space_id,
            "asset_name": asset_name,
            "row_count": len(rows_dicts),
            "top": top,
        }

        return QueryResult(columns=columns, rows=rows, truncated=truncated, meta=meta)

    async def get_relational_metadata(
        self,
        space_id: str,
        asset_name: str,
    ) -> str:
        """Fetch the OData $metadata document for a relational asset."""
        token = await self.oauth.get_access_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/xml",
        }

        urls: List[str] = []
        for prefix in self._consumption_prefixes():
            urls.append(f"{prefix}/relational/{space_id}/{asset_name}/$metadata")
            urls.append(f"{prefix}/relational/{space_id}/{asset_name}/{space_id}/{asset_name}/$metadata")

        response = await self._get_with_fallback(
            urls=urls,
            headers=headers,
            params=None,
            timeout_seconds=60.0,
            allow_top_fallback=False,
        )
        return response.text

    # ------------------------------------------------------------------
    # Relational query API
    # ------------------------------------------------------------------

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
        """Run a relational query using the relational consumption API."""
        token = await self.oauth.get_access_token()

        params: Dict[str, Any] = {}
        if top is not None:
            params["$top"] = int(top)
        if skip:
            params["$skip"] = int(skip)
        if select:
            params["$select"] = ",".join(select)
        if filter_expr:
            params["$filter"] = filter_expr
        if order_by:
            params["$orderby"] = order_by

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        urls: List[str] = []
        for prefix in self._consumption_prefixes():
            urls.append(f"{prefix}/relational/{space_id}/{asset_name}/{asset_name}")
            urls.append(f"{prefix}/relational/{space_id}/{asset_name}/{space_id}/{asset_name}/{asset_name}")

        response = await self._get_with_fallback(
            urls=urls,
            headers=headers,
            params=params or None,
            timeout_seconds=60.0,
            allow_top_fallback=True,
        )

        data = response.json()
        raw_rows = data.get("value") if isinstance(data, dict) else data

        rows_dicts: List[Dict[str, Any]] = []
        if isinstance(raw_rows, list):
            rows_dicts = [r for r in raw_rows if isinstance(r, dict)]

        if not rows_dicts:
            return QueryResult(
                columns=[],
                rows=[],
                truncated=False,
                meta={
                    "space_id": space_id,
                    "asset_name": asset_name,
                    "row_count": 0,
                    "top": top,
                    "skip": skip,
                    "filter": filter_expr,
                    "order_by": order_by,
                },
            )

        columns = list(rows_dicts[0].keys())
        rows = [[row.get(col) for col in columns] for row in rows_dicts]
        truncated = top is not None and len(rows) >= top

        meta = {
            "space_id": space_id,
            "asset_name": asset_name,
            "row_count": len(rows_dicts),
            "top": top,
            "skip": skip,
            "filter": filter_expr,
            "order_by": order_by,
        }

        return QueryResult(columns=columns, rows=rows, truncated=truncated, meta=meta)

    # ------------------------------------------------------------------
    # Analytical query API (v0.3+)
    # ------------------------------------------------------------------

    async def query_analytical(
        self,
        space_id: str,
        asset_name: str,
        select: Iterable[str] | None = None,
        filter_expr: str | None = None,
        order_by: str | None = None,
        top: int = 100,
        skip: int = 0,
    ) -> QueryResult:
        """Run an analytical query (consumption/analytical) against an analytic model."""
        token = await self.oauth.get_access_token()

        params: Dict[str, Any] = {}
        if top is not None:
            params["$top"] = int(top)
        if skip:
            params["$skip"] = int(skip)
        if select:
            params["$select"] = ",".join(select)
        if filter_expr:
            params["$filter"] = filter_expr
        if order_by:
            params["$orderby"] = order_by

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        urls: List[str] = []
        for prefix in self._consumption_prefixes():
            urls.append(f"{prefix}/analytical/{space_id}/{asset_name}/{asset_name}")

        response = await self._get_with_fallback(
            urls=urls,
            headers=headers,
            params=params or None,
            timeout_seconds=60.0,
            allow_top_fallback=True,
        )

        data = response.json()
        raw_rows = data.get("value") if isinstance(data, dict) else data

        rows_dicts: List[Dict[str, Any]] = []
        if isinstance(raw_rows, list):
            rows_dicts = [r for r in raw_rows if isinstance(r, dict)]

        if not rows_dicts:
            return QueryResult(
                columns=[],
                rows=[],
                truncated=False,
                meta={
                    "space_id": space_id,
                    "asset_name": asset_name,
                    "row_count": 0,
                    "top": top,
                    "skip": skip,
                    "filter": filter_expr,
                    "order_by": order_by,
                    "mode": "analytical",
                },
            )

        columns = list(rows_dicts[0].keys())
        rows = [[row.get(col) for col in columns] for row in rows_dicts]
        truncated = top is not None and len(rows) >= top

        meta = {
            "space_id": space_id,
            "asset_name": asset_name,
            "row_count": len(rows_dicts),
            "top": top,
            "skip": skip,
            "filter": filter_expr,
            "order_by": order_by,
            "mode": "analytical",
        }

        return QueryResult(columns=columns, rows=rows, truncated=truncated, meta=meta)
