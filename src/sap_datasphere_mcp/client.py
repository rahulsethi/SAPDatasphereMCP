# SAP Datasphere MCP Server
# File: client.py
# Version: v9
"""High-level client for SAP Datasphere REST APIs.

Implements:

- list_spaces() via the Catalog API
- list_space_assets() via the Catalog API
- preview_asset_data() via the relational Consumption API
- query_relational() via the relational Consumption API
- get_catalog_asset() for per-asset catalog metadata
- get_relational_metadata() for relational OData $metadata
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

import httpx
from httpx import HTTPStatusError, RequestError

from .auth import OAuthClient
from .config import DatasphereConfig
from .models import Asset, QueryResult, Space


@dataclass
class DatasphereClient:
    """Wrapper around SAP Datasphere catalog and consumption APIs."""

    config: DatasphereConfig
    oauth: OAuthClient

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
        if not self.config.tenant_url:
            raise RuntimeError(
                "DATASPHERE_TENANT_URL is not set. "
                "Please configure it before calling list_spaces()."
            )

        token = await self.oauth.get_access_token()
        base_url = self.config.tenant_url.rstrip("/")
        url = f"{base_url}/api/v1/dwc/catalog/spaces"

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(timeout=30.0) as http_client:
            try:
                response = await http_client.get(url, headers=headers)
            except RequestError as exc:
                raise RuntimeError(
                    f"Error calling Datasphere catalog API at '{url}': {exc}"
                ) from exc

            try:
                response.raise_for_status()
            except HTTPStatusError as exc:
                status = response.status_code
                body_preview = response.text[:500]
                raise RuntimeError(
                    "Failed to list spaces from "
                    f"'{url}' (HTTP {status}). "
                    f"Response snippet: {body_preview}"
                ) from exc

        data = response.json()
        raw_spaces = data.get("value") if isinstance(data, dict) else data

        spaces: List[Space] = []
        if isinstance(raw_spaces, list):
            for item in raw_spaces:
                if not isinstance(item, dict):
                    continue

                space_id = (
                    item.get("id")
                    or item.get("technicalName")
                    or item.get("name")
                )
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
        """List catalog assets within a given Datasphere space.

        Uses the Catalog API endpoint:

        /api/v1/dwc/catalog/spaces('<space_id>')/assets
        """
        if not self.config.tenant_url:
            raise RuntimeError(
                "DATASPHERE_TENANT_URL is not set. "
                "Please configure it before calling list_space_assets()."
            )

        token = await self.oauth.get_access_token()
        base_url = self.config.tenant_url.rstrip("/")

        # Single quotes must be escaped for OData key literals.
        key_space_id = space_id.replace("'", "''")
        url = (
            f"{base_url}/api/v1/dwc/catalog/"
            f"spaces('{key_space_id}')/assets"
        )

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(timeout=30.0) as http_client:
            try:
                response = await http_client.get(url, headers=headers)
            except RequestError as exc:
                raise RuntimeError(
                    f"Error calling Datasphere catalog API at '{url}': {exc}"
                ) from exc

            try:
                response.raise_for_status()
            except HTTPStatusError as exc:
                status = response.status_code
                body_preview = response.text[:500]
                raise RuntimeError(
                    "Failed to list assets for space "
                    f"'{space_id}' from '{url}' (HTTP {status}). "
                    f"Response snippet: {body_preview}"
                ) from exc

        data = response.json()
        raw_assets = data.get("value") if isinstance(data, dict) else data

        assets: List[Asset] = []
        if isinstance(raw_assets, list):
            for item in raw_assets:
                if not isinstance(item, dict):
                    continue

                asset_id = (
                    item.get("id")
                    or item.get("technicalName")
                    or item.get("name")
                )
                name = item.get("name") or asset_id or ""
                asset_type = (
                    item.get("type")
                    or item.get("assetType")
                    or item.get("kind")
                )
                description = item.get("description")

                assets.append(
                    Asset(
                        id=str(asset_id),
                        name=str(name),
                        type=str(asset_type)
                        if asset_type is not None
                        else None,
                        space_id=space_id,
                        description=description,
                        raw=item,
                    )
                )

        return assets

    async def get_catalog_asset(self, space_id: str, asset_id: str) -> Dict[str, Any]:
        """Get catalog metadata for a single asset in a space.

        This uses the same Catalog API family as list_space_assets but
        targets the single-asset endpoint:

        /api/v1/dwc/catalog/spaces('<space_id>')/assets('<asset_id>')

        The raw JSON payload is returned so higher layers (MCP tools) can
        expose whichever fields are useful, such as:

        - name / label / description
        - type / semantic usage
        - assetRelationalMetadataUrl / assetRelationalDataUrl
        - assetAnalyticalMetadataUrl / assetAnalyticalDataUrl
        """
        if not self.config.tenant_url:
            raise RuntimeError(
                "DATASPHERE_TENANT_URL is not set. "
                "Please configure it before calling get_catalog_asset()."
            )

        token = await self.oauth.get_access_token()
        base_url = self.config.tenant_url.rstrip("/")

        key_space_id = space_id.replace("'", "''")
        key_asset_id = asset_id.replace("'", "''")

        url = (
            f"{base_url}/api/v1/dwc/catalog/"
            f"spaces('{key_space_id}')/assets('{key_asset_id}')"
        )

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(timeout=30.0) as http_client:
            try:
                response = await http_client.get(url, headers=headers)
            except RequestError as exc:
                raise RuntimeError(
                    "Error calling Datasphere catalog API for asset "
                    f"'{asset_id}' in space '{space_id}' at '{url}': {exc}"
                ) from exc

            try:
                response.raise_for_status()
            except HTTPStatusError as exc:
                status = response.status_code
                body_preview = response.text[:500]
                raise RuntimeError(
                    "Failed to fetch catalog metadata for asset "
                    f"'{asset_id}' in space '{space_id}' from "
                    f"'{url}' (HTTP {status}). "
                    f"Response snippet: {body_preview}"
                ) from exc

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
        """Fetch a small sample of rows from a Datasphere asset.

        Uses the Relational Consumption API endpoint:

        /api/v1/dwc/consumption/relational/<space_id>/<asset_name>/<asset_name>

        We add a $top parameter by default. If the service responds with a
        400 complaining that $top is not supported, we retry once without
        it.

        Not all assets are exposed via this endpoint; some may return 404
        or other errors even though they are visible in the catalog UI.
        """
        if not self.config.tenant_url:
            raise RuntimeError(
                "DATASPHERE_TENANT_URL is not set. "
                "Please configure it before calling preview_asset_data()."
            )

        token = await self.oauth.get_access_token()
        base_url = self.config.tenant_url.rstrip("/")
        url = (
            f"{base_url}/api/v1/dwc/consumption/relational/"
            f"{space_id}/{asset_name}/{asset_name}"
        )

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

        async with httpx.AsyncClient(timeout=60.0) as http_client:
            try:
                # First attempt (with $top if provided)
                response = await http_client.get(
                    url, headers=headers, params=params or None
                )

                # If the service says "$top is not supported", retry without it
                if (
                    response.status_code == 400
                    and "Query option '$top' is not supported"
                    in (response.text or "")
                ):
                    params.pop("$top", None)
                    response = await http_client.get(
                        url, headers=headers, params=params or None
                    )
            except RequestError as exc:
                raise RuntimeError(
                    "Error calling Datasphere consumption API for asset "
                    f"'{asset_name}' in space '{space_id}': {exc}"
                ) from exc

            try:
                response.raise_for_status()
            except HTTPStatusError as exc:
                status = response.status_code
                body_preview = response.text[:500]
                raise RuntimeError(
                    "Failed to preview data for asset "
                    f"'{asset_name}' in space '{space_id}' from "
                    f"'{url}' (HTTP {status}). "
                    f"Response snippet: {body_preview}"
                ) from exc

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

        # Derive column order from the first row.
        columns = list(rows_dicts[0].keys())
        rows = [[row.get(col) for col in columns] for row in rows_dicts]
        truncated = top is not None and len(rows) >= top

        meta = {
            "space_id": space_id,
            "asset_name": asset_name,
            "row_count": len(rows_dicts),
            "top": top,
        }

        return QueryResult(
            columns=columns,
            rows=rows,
            truncated=truncated,
            meta=meta,
        )

    async def get_relational_metadata(
        self,
        space_id: str,
        asset_name: str,
    ) -> str:
        """Fetch the OData $metadata document for a relational asset.

        This calls the relational Consumption API metadata endpoint:

        /api/v1/dwc/consumption/relational/<space_id>/<asset_name>/$metadata

        The raw XML (EDMX) payload is returned as a string so that
        higher layers can parse it as needed (column list, labels, etc.).
        """
        if not self.config.tenant_url:
            raise RuntimeError(
                "DATASPHERE_TENANT_URL is not set. "
                "Please configure it before calling get_relational_metadata()."
            )

        token = await self.oauth.get_access_token()
        base_url = self.config.tenant_url.rstrip("/")
        url = (
            f"{base_url}/api/v1/dwc/consumption/relational/"
            f"{space_id}/{asset_name}/$metadata"
        )

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/xml",
        }

        async with httpx.AsyncClient(timeout=60.0) as http_client:
            try:
                response = await http_client.get(url, headers=headers)
            except RequestError as exc:
                raise RuntimeError(
                    "Error calling Datasphere relational metadata endpoint "
                    f"for asset '{asset_name}' in space '{space_id}' at "
                    f"'{url}': {exc}"
                ) from exc

            try:
                response.raise_for_status()
            except HTTPStatusError as exc:
                status = response.status_code
                body_preview = response.text[:500]
                raise RuntimeError(
                    "Failed to fetch relational metadata for asset "
                    f"'{asset_name}' in space '{space_id}' from "
                    f"'{url}' (HTTP {status}). "
                    f"Response snippet: {body_preview}"
                ) from exc

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
        """Run a relational query using the relational consumption API.

        Supports:

        - $top / $skip (paging)
        - $filter (OData-style filter)
        - $orderby (OData-style order by)
        - $select (projection)
        """
        if not self.config.tenant_url:
            raise RuntimeError(
                "DATASPHERE_TENANT_URL is not set. "
                "Please configure it before calling query_relational()."
            )

        token = await self.oauth.get_access_token()
        base_url = self.config.tenant_url.rstrip("/")
        url = (
            f"{base_url}/api/v1/dwc/consumption/relational/"
            f"{space_id}/{asset_name}/{asset_name}"
        )

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

        async with httpx.AsyncClient(timeout=60.0) as http_client:
            try:
                response = await http_client.get(
                    url, headers=headers, params=params or None
                )

                # Same $top retry logic as preview, just in case
                if (
                    response.status_code == 400
                    and "Query option '$top' is not supported"
                    in (response.text or "")
                    and "$top" in params
                ):
                    params.pop("$top", None)
                    response = await http_client.get(
                        url, headers=headers, params=params or None
                    )
            except RequestError as exc:
                raise RuntimeError(
                    "Error calling Datasphere consumption API for asset "
                    f"'{asset_name}' in space '{space_id}' "
                    f"(query_relational): {exc}"
                ) from exc

            try:
                response.raise_for_status()
            except HTTPStatusError as exc:
                status = response.status_code
                body_preview = response.text[:500]
                raise RuntimeError(
                    "Failed to run relational query for asset "
                    f"'{asset_name}' in space '{space_id}' from "
                    f"'{url}' (HTTP {status}). "
                    f"Response snippet: {body_preview}"
                ) from exc

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

        return QueryResult(
            columns=columns,
            rows=rows,
            truncated=truncated,
            meta=meta,
        )
