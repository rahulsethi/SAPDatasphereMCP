# SAP Datasphere MCP Server
# File: prompts/__init__.py
# Version: v1 (1.0)

"""MCP Prompts package.

Each prompt module exposes ``PROMPT`` (a metadata dict) and ``render(args)``
returning a list of MCP user messages. :func:`register` wires all of them
into a FastMCP server.

Shipping prompts is a first-in-class differentiator for the SAP MCP space —
no other SAP-ecosystem MCP server (including the competing
``MarioDeFelipe/sap-datasphere-mcp``) ships prompts at the time of v1.0.
"""

from __future__ import annotations

import logging
from typing import Any

from . import (
    audit_space,
    compare_assets,
    explain_analytical_model,
    find_data_about_topic,
    profile_dataset,
)

__all__ = ["register", "ALL_PROMPTS"]

log = logging.getLogger("sap_datasphere_mcp.prompts")

ALL_PROMPTS = [
    profile_dataset,
    audit_space,
    explain_analytical_model,
    compare_assets,
    find_data_about_topic,
]


def register(server: Any) -> None:
    """Register every prompt module on ``server``.

    Gracefully no-ops on MCP SDKs without prompt support; logs a warning
    so the rest of the server still starts.
    """
    if not hasattr(server, "prompt"):
        log.warning("MCP server lacks .prompt() — skipping prompt registration; upgrade mcp[cli] for prompt support.")
        return

    for mod in ALL_PROMPTS:
        meta = mod.PROMPT
        render_fn = mod.render
        try:
            decorator = server.prompt(name=meta["name"], description=meta["description"])
        except TypeError:
            decorator = server.prompt(meta["name"])
        decorator(render_fn)
