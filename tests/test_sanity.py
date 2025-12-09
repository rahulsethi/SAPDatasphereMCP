# SAP Datasphere MCP Server
# File: tests/test_sanity.py
# Version: v1

"""Basic sanity tests for the initial scaffolding."""

from sap_datasphere_mcp.config import DatasphereConfig
from sap_datasphere_mcp.auth import OAuthClient
from sap_datasphere_mcp.client import DatasphereClient


def test_config_from_env_minimal() -> None:
    config = DatasphereConfig.from_env()
    assert config is not None


def test_client_ping_runs() -> None:
    config = DatasphereConfig.from_env()
    oauth = OAuthClient(config=config)
    client = DatasphereClient(config=config, oauth=oauth)

    # ping should always return a boolean
    # even if tenant_url is not yet configured.
    import asyncio

    result = asyncio.run(client.ping())
    assert isinstance(result, bool)
