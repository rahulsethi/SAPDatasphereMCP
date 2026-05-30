# SAP Datasphere MCP Server
# File: transports/http_server.py
# Version: v3 (1.0)

"""HTTP entrypoint for the SAP Datasphere MCP server.

Backed by :func:`sap_datasphere_mcp.server.create_server` so stdio and HTTP
boot identically. v1.0 additions:

- Optional bearer-token gate via ``DATASPHERE_MCP_BEARER_TOKEN``. When set,
  the SDK is configured to require ``Authorization: Bearer <token>`` on every
  request. We do not roll our own auth — we hand the token to FastMCP if it
  exposes a hook, and surface a clear error if not.

Configured via environment variables:

- ``DATASPHERE_MCP_TRANSPORT``       — ``streamable-http`` (default) or ``sse``
- ``DATASPHERE_MCP_HOST``            — ``127.0.0.1``
- ``DATASPHERE_MCP_PORT``            — ``8000``
- ``DATASPHERE_MCP_LOG_LEVEL``       — ``INFO`` (default) / ``DEBUG`` / ``WARNING`` / ``ERROR``
- ``DATASPHERE_MCP_BEARER_TOKEN``    — optional shared bearer required by HTTP clients
"""

from __future__ import annotations

import inspect
import logging
import os
from typing import Any, Dict, Optional

from ..server import create_server


def _parse_int_env(name: str, default: int, *, min_value: int = 1, max_value: int = 65535) -> int:
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        value = int(default)
    else:
        try:
            value = int(str(raw).strip())
        except ValueError:
            value = int(default)
    if value < min_value:
        value = min_value
    if value > max_value:
        value = max_value
    return value


def _setup_logging() -> None:
    level = (os.getenv("DATASPHERE_MCP_LOG_LEVEL") or "INFO").strip().upper()
    if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        level = "INFO"
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )


def _normalise_transport(raw: Optional[str]) -> str:
    t = (raw or "streamable-http").strip().lower().replace("_", "-")
    if t in {"http", "streamable", "streamablehttp"}:
        return "streamable-http"
    return t


def _maybe_apply_bearer(mcp: Any, token: Optional[str], logger: logging.Logger) -> None:
    """Best-effort wiring of the bearer-token gate.

    Different MCP SDK versions expose this differently. We probe a few common
    attributes and degrade to a clear warning if none of them are present.
    """
    if not token:
        return
    # FastMCP variants we have seen across versions:
    for attr in ("set_auth_token", "set_bearer_token", "set_auth"):
        hook = getattr(mcp, attr, None)
        if callable(hook):
            try:
                hook(token)
                logger.info("HTTP transport bearer auth enabled via %s", attr)
                return
            except Exception as exc:  # pragma: no cover
                logger.warning("%s rejected the bearer token: %s", attr, exc)
                break

    # Property-style: mcp.auth = {...}
    if hasattr(mcp, "auth"):
        try:
            mcp.auth = {"scheme": "bearer", "token": token}
            logger.info("HTTP transport bearer auth enabled via mcp.auth attribute")
            return
        except Exception as exc:  # pragma: no cover
            logger.warning("mcp.auth assignment rejected: %s", exc)

    logger.warning(
        "DATASPHERE_MCP_BEARER_TOKEN is set, but the installed mcp SDK exposes no auth hook. "
        "Deploy this server behind a reverse proxy that enforces bearer auth, or upgrade mcp[cli]."
    )


def _run_server(mcp: Any, transport: str, host: str, port: int) -> None:
    """Run FastMCP over the selected HTTP transport with best-effort compatibility."""
    try:
        sig = inspect.signature(mcp.run)
        kwargs: Dict[str, Any] = {}
        if "transport" in sig.parameters:
            kwargs["transport"] = transport
        if "host" in sig.parameters:
            kwargs["host"] = host
        if "port" in sig.parameters:
            kwargs["port"] = port

        if "transport" not in sig.parameters:
            raise TypeError("FastMCP.run() does not expose a 'transport' parameter in this SDK.")

        mcp.run(**kwargs)
        return
    except TypeError:
        method = None
        if transport == "sse":
            method = getattr(mcp, "run_sse", None)
        elif transport == "streamable-http":
            method = getattr(mcp, "run_streamable_http", None)

        if callable(method):
            try:
                msig = inspect.signature(method)
                kwargs2: Dict[str, Any] = {}
                if "host" in msig.parameters:
                    kwargs2["host"] = host
                if "port" in msig.parameters:
                    kwargs2["port"] = port
                method(**kwargs2)
                return
            except Exception as exc:
                raise RuntimeError(f"Failed to run FastMCP via {method.__name__}(): {exc}") from exc

        raise RuntimeError(
            "Your installed MCP Python SDK does not appear to support HTTP transports "
            "(streamable-http or sse). Upgrade the 'mcp[cli]' package to >=1.25.0."
        )


def main() -> int:
    """Synchronous entrypoint for the HTTP transport."""
    _setup_logging()
    logger = logging.getLogger(__name__)

    host = (os.getenv("DATASPHERE_MCP_HOST") or "127.0.0.1").strip()
    port = _parse_int_env("DATASPHERE_MCP_PORT", 8000)
    transport = _normalise_transport(os.getenv("DATASPHERE_MCP_TRANSPORT"))
    bearer = os.getenv("DATASPHERE_MCP_BEARER_TOKEN") or None

    if transport not in {"streamable-http", "sse"}:
        raise ValueError(
            f"Unsupported DATASPHERE_MCP_TRANSPORT='{transport}'. Supported: streamable-http, sse"
        )

    mcp = create_server()
    _maybe_apply_bearer(mcp, bearer, logger)

    logger.info(
        "Starting MCP HTTP server transport=%s host=%s port=%s bearer=%s",
        transport,
        host,
        port,
        "set" if bearer else "unset",
    )
    _run_server(mcp, transport=transport, host=host, port=port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
