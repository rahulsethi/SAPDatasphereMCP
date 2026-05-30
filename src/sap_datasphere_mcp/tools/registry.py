# SAP Datasphere MCP Server
# File: tools/registry.py
# Version: v1 (1.0)

"""Central MCP tool registry.

Replaces v0.3.x's ``tasks.register_tools``. The function
:func:`register_all` registers every v1.0 tool under its canonical name
*and* under each legacy v0.3.x alias.

Old direct callers of ``tasks.register_tools(server)`` continue to work for
back-compat (it delegates here under the hood, see :mod:`.tasks`).
"""

from __future__ import annotations

import logging
from typing import Any, Iterable, List, Tuple

from . import _aliases, _gated, catalog, connectivity, discover, governance, profile, query, summarize
from ._metadata import ToolMetadata

__all__ = ["register_all", "CATEGORY_MODULES"]

log = logging.getLogger("sap_datasphere_mcp.tools.registry")

CATEGORY_MODULES = [connectivity, catalog, query, discover, profile, summarize, governance]


def _try_annotations(meta: ToolMetadata) -> dict:
    """Build an MCP ToolAnnotations dict from per-tool metadata.

    Returned as a plain dict because we pass it to whatever annotation shape
    the MCP SDK supports at runtime; the SDK does its own validation.
    """
    return {
        "title": meta.description.split(".")[0][:80],
        "readOnlyHint": meta.read_only,
        "idempotentHint": meta.idempotent,
        "destructiveHint": meta.destructive,
        "openWorldHint": meta.open_world,
    }


def _register_one(server: Any, meta: ToolMetadata, fn) -> None:
    wrapped = _gated.wrap_tool(meta, fn)
    annotations = _try_annotations(meta)

    # Try the modern MCP SDK signature (with annotations); fall back gracefully.
    try:
        decorator = server.tool(name=meta.name, description=meta.description, annotations=annotations)
    except TypeError:
        try:
            decorator = server.tool(name=meta.name, description=meta.description)
        except Exception:
            decorator = server.tool(meta.name)
    decorator(wrapped)


def _register_alias(server: Any, legacy_name: str, target_meta: ToolMetadata, target_fn) -> None:
    wrapped_target = _gated.wrap_tool(target_meta, target_fn)
    alias_fn = _gated.make_alias(legacy_name, target_meta, wrapped_target)
    desc = f"DEPRECATED — use `{target_meta.name}` instead. Removed in v1.2. {target_meta.description}"

    annotations = _try_annotations(target_meta)
    try:
        decorator = server.tool(name=legacy_name, description=desc, annotations=annotations)
    except TypeError:
        try:
            decorator = server.tool(name=legacy_name, description=desc)
        except Exception:
            decorator = server.tool(legacy_name)
    decorator(alias_fn)


def _all_bindings() -> Iterable[Tuple[ToolMetadata, Any]]:
    for mod in CATEGORY_MODULES:
        yield from mod.BINDINGS


def register_all(server: Any) -> None:
    """Register every v1.0 tool plus every legacy alias on ``server``.

    ``server`` must expose a ``.tool(name=..., description=...)`` decorator
    in the style of FastMCP.
    """
    if not hasattr(server, "tool"):
        raise TypeError("register_all(server) expects an MCP server-like object exposing a .tool() decorator.")

    # 1) canonical v1.0 names
    canonical_count = 0
    for meta, fn in _all_bindings():
        _register_one(server, meta, fn)
        canonical_count += 1

    # 2) legacy aliases (so 0.3.x clients keep working through 1.1)
    alias_count = 0
    canonical_lookup = {meta.name: (meta, fn) for meta, fn in _all_bindings()}
    for legacy_name, canonical_name in _aliases.LEGACY_ALIASES.items():
        pair = canonical_lookup.get(canonical_name)
        if pair is None:  # pragma: no cover — guarded by _metadata registry
            log.warning("alias '%s' points to unknown canonical name '%s'; skipping", legacy_name, canonical_name)
            continue
        meta, fn = pair
        _register_alias(server, legacy_name, meta, fn)
        alias_count += 1

    log.info("registered %d canonical tools and %d legacy aliases", canonical_count, alias_count)
