# SAP Datasphere MCP Server
# File: tools/_aliases.py
# Version: v1 (1.0)

"""Legacy (v0.3.x) → canonical (v1.0) tool name aliases.

Built from ``_metadata.TOOL_REGISTRY`` so there is exactly one source of
truth. Aliases are registered alongside the canonical names by
:func:`tools.registry.register_all`; calling an alias emits a one-time
structured-log warning and forwards to the v1.0 implementation. Aliases are
removed in v1.2.
"""

from __future__ import annotations

from typing import Dict

from ._metadata import iter_tools

__all__ = ["LEGACY_ALIASES"]


def _build_aliases() -> Dict[str, str]:
    out: Dict[str, str] = {}
    for canonical_name, meta in iter_tools():
        if meta.legacy_name and meta.legacy_name != canonical_name:
            out[meta.legacy_name] = canonical_name
    return out


#: Mapping: legacy_name -> canonical_name. Read-only.
LEGACY_ALIASES: Dict[str, str] = _build_aliases()
