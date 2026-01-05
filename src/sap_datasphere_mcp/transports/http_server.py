# SAP Datasphere MCP Server
# File: transports/http_server.py
# Version: v2

"""HTTP entrypoint for the SAP Datasphere MCP server.

This transport lets you run the MCP server over HTTP instead of stdio.

Supported transports (depends on your installed MCP Python SDK version):
- "streamable-http" (recommended)
- "sse"

Configured via environment variables:
  DATASPHERE_MCP_TRANSPORT   = streamable-http | sse
  DATASPHERE_MCP_HOST        = 127.0.0.1
  DATASPHERE_MCP_PORT        = 8000
  DATASPHERE_MCP_LOG_LEVEL   = INFO | DEBUG | WARNING | ERROR
"""

from __future__ import annotations

import inspect
import logging
import os
from typing import Any, Dict, Optional

from mcp.server.fastmcp import FastMCP

from ..plugins import registry as plugin_registry
from ..tools import tasks


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
    # common aliases people try:
    if t in {"http", "streamable", "streamablehttp"}:
        return "streamable-http"
    return t


def _create_server(name: str, host: str, port: int) -> FastMCP:
    """Create FastMCP, supporting SDKs that accept host/port either in ctor or run()."""
    try:
        return FastMCP(name, host=host, port=port)  # type: ignore[call-arg]
    except TypeError:
        return FastMCP(name)


def _run_server(mcp: FastMCP, transport: str, host: str, port: int) -> None:
    """Run FastMCP over the selected HTTP transport with best-effort compatibility."""
    # Preferred path: FastMCP.run(transport=..., host=..., port=...)
    try:
        sig = inspect.signature(mcp.run)
        kwargs: Dict[str, Any] = {}
        if "transport" in sig.parameters:
            kwargs["transport"] = transport
        if "host" in sig.parameters:
            kwargs["host"] = host
        if "port" in sig.parameters:
            kwargs["port"] = port

        # If transport isn't supported by this SDK, avoid silently running stdio.
        if "transport" not in sig.parameters:
            raise TypeError("FastMCP.run() does not expose a 'transport' parameter in this SDK.")

        mcp.run(**kwargs)
        return
    except TypeError:
        # Fallbacks for older/newer APIs that expose dedicated run_* helpers.
        method = None
        if transport == "sse":
            method = getattr(mcp, "run_sse", None)
        elif transport == "streamable-http":
            method = getattr(mcp, "run_streamable_http", None) or getattr(mcp, "run_streamable-http", None)

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
            "(streamable-http or sse) via FastMCP. "
            "Upgrade the 'mcp' package to a version that supports HTTP transports."
        )


def main() -> None:
    """Synchronous entrypoint for an HTTP-based MCP server."""
    _setup_logging()
    logger = logging.getLogger(__name__)

    host = (os.getenv("DATASPHERE_MCP_HOST") or "127.0.0.1").strip()
    port = _parse_int_env("DATASPHERE_MCP_PORT", 8000)
    transport = _normalise_transport(os.getenv("DATASPHERE_MCP_TRANSPORT"))

    if transport not in {"streamable-http", "sse"}:
        raise ValueError(
            f"Unsupported DATASPHERE_MCP_TRANSPORT='{transport}'. "
            "Supported: streamable-http, sse"
        )

    mcp = _create_server("sap-datasphere-mcp", host=host, port=port)

    # Register core MCP tools
    tasks.register_tools(mcp)

    # Load optional plugins (must never crash the core server).
    plugin_registry.register_plugins(mcp)

    logger.info("Starting MCP HTTP server transport=%s host=%s port=%s", transport, host, port)
    _run_server(mcp, transport=transport, host=host, port=port)


if __name__ == "__main__":
    main()
