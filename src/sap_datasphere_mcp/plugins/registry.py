# SAP Datasphere MCP Server
# File: plugins/registry.py
# Version: v1

"""Plugin registry & loader for the SAP Datasphere MCP Server.

Configured via:
  DATASPHERE_PLUGINS="module.one,module.two"

Each plugin module must expose:
  register_tools(server) -> None

Design rules:
- Plugin failures must never crash the core server.
- Status should be queryable later (e.g., diagnostics in v0.3).
"""

from __future__ import annotations

import importlib
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PluginStatus:
    name: str
    ok: bool
    error: Optional[str] = None


_PLUGIN_STATUS: List[PluginStatus] = []


def get_configured_plugins() -> List[str]:
    """Return a cleaned list of plugin module names from DATASPHERE_PLUGINS."""
    raw = os.getenv("DATASPHERE_PLUGINS", "") or ""
    if not raw.strip():
        return []

    items = [p.strip() for p in raw.split(",")]
    return [p for p in items if p]


def get_plugin_status() -> List[Dict[str, Any]]:
    """Return the last plugin load attempt as JSON-serialisable dicts."""
    return [
        {"name": s.name, "ok": s.ok, "error": s.error}
        for s in list(_PLUGIN_STATUS)
    ]


def register_plugins(server: Any) -> Dict[str, Any]:
    """Load and register plugins against the given MCP server.

    Returns a small status report:
      {"plugins": [...], "loaded": int, "failed": int}
    """
    global _PLUGIN_STATUS
    _PLUGIN_STATUS = []

    plugins = get_configured_plugins()
    if not plugins:
        logger.info("No plugins configured (DATASPHERE_PLUGINS is empty).")
        return {"plugins": [], "loaded": 0, "failed": 0}

    loaded = 0
    failed = 0

    for module_name in plugins:
        try:
            module = importlib.import_module(module_name)
            register_tools = getattr(module, "register_tools", None)

            if not callable(register_tools):
                failed += 1
                msg = "Module does not export callable register_tools(server)."
                _PLUGIN_STATUS.append(
                    PluginStatus(name=module_name, ok=False, error=msg)
                )
                logger.warning(
                    "Plugin '%s' missing register_tools(server); skipping.",
                    module_name,
                )
                continue

            register_tools(server)
            loaded += 1
            _PLUGIN_STATUS.append(PluginStatus(name=module_name, ok=True))
            logger.info("Loaded plugin: %s", module_name)

        except Exception as exc:  # defensive: plugins must not crash core
            failed += 1
            _PLUGIN_STATUS.append(
                PluginStatus(name=module_name, ok=False, error=str(exc))
            )
            logger.warning(
                "Failed to load plugin '%s': %s",
                module_name,
                exc,
                exc_info=True,
            )

    return {"plugins": get_plugin_status(), "loaded": loaded, "failed": failed}
