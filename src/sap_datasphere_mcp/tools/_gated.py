# SAP Datasphere MCP Server
# File: tools/_gated.py
# Version: v1 (1.0)

"""Per-tool interceptor chain: policy gate → audit start → tool → redaction → audit commit.

Implemented as a thin decorator-stack wrapper. The wrapper preserves the
underlying function's signature via ``functools.wraps`` + ``__wrapped__`` so
FastMCP's introspection still sees the original arg names and types.
"""

from __future__ import annotations

import functools
import inspect
import logging
import os
from typing import Any, Awaitable, Callable, Dict, Optional

from .. import audit, policy, redaction
from ._metadata import ToolMetadata

__all__ = ["wrap_tool", "ALIAS_LOG_KEY"]

log = logging.getLogger("sap_datasphere_mcp.tools")

ALIAS_LOG_KEY = "_dsa_alias_logged"


def _oauth_sub() -> Optional[str]:
    """Best-effort OAuth client identifier for the audit log."""
    if os.environ.get("DATASPHERE_MOCK_MODE", "").strip().lower() in {"1", "true", "yes", "on"}:
        return "mock"
    cid = os.environ.get("DATASPHERE_CLIENT_ID")
    if not cid:
        return None
    # Match the client_id at the | separator used by BTP UAA scopes.
    return cid.split("|", 1)[-1] if "|" in cid else cid


def _tenant_url() -> Optional[str]:
    return os.environ.get("DATASPHERE_TENANT_URL")


def _maybe_rows(result: Any) -> Optional[int]:
    """Heuristic: count rows in common tool return shapes."""
    if isinstance(result, dict):
        rows = result.get("rows")
        if isinstance(rows, list):
            return len(rows)
        # Common pattern: { "items": [...] }
        items = result.get("items") or result.get("assets") or result.get("spaces") or result.get("columns")
        if isinstance(items, list):
            return len(items)
    return None


def wrap_tool(meta: ToolMetadata, fn: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
    """Wrap ``fn`` with the policy / audit / redaction interceptor chain.

    The returned coroutine:

    1. Refuses the call if the policy gate rejects it (returns a structured
       error dict matching :func:`PolicyDecision.as_error`).
    2. Starts an audit record (no-op when audit is disabled).
    3. Awaits the underlying function.
    4. Scrubs the result via :mod:`redaction`.
    5. Commits the audit record with outcome + rough row count.
    """
    sig = inspect.signature(fn)
    audit_log = audit.get_audit_log()

    @functools.wraps(fn)
    async def wrapped(*args: Any, **kwargs: Any) -> Any:
        # Bind for the audit fingerprint and tidy kwargs dict.
        try:
            bound = sig.bind_partial(*args, **kwargs)
            bound.apply_defaults()
            named_args: Dict[str, Any] = dict(bound.arguments)
        except TypeError:
            named_args = {"args": args, "kwargs": kwargs}

        decision = policy.permits(meta.name, policy_class=meta.policy_class)
        if not decision.allowed:
            err = decision.as_error()
            rec = audit_log.start(
                tool=meta.name,
                sub=_oauth_sub(),
                tenant_url=_tenant_url(),
                policy_strict=policy.is_strict(),
                args=named_args,
            )
            audit_log.commit(rec, outcome="denied", error_code="policy_denied")
            return err

        rec = audit_log.start(
            tool=meta.name,
            sub=_oauth_sub(),
            tenant_url=_tenant_url(),
            policy_strict=policy.is_strict(),
            args=named_args,
        )
        try:
            result = await fn(*args, **kwargs)
        except Exception as exc:  # pragma: no cover — defensive
            audit_log.commit(rec, outcome="error", error_code=type(exc).__name__)
            raise

        scrubbed = redaction.scrub(result)
        audit_log.commit(rec, outcome="ok", rows=_maybe_rows(scrubbed))
        return scrubbed

    wrapped.__wrapped__ = fn  # ensure inspect.signature follows through
    return wrapped


def make_alias(legacy_name: str, target_meta: ToolMetadata, wrapped_target: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
    """Return an async alias wrapper that logs a one-time deprecation warning."""
    _logged = {"once": False}

    @functools.wraps(wrapped_target)
    async def alias(*args: Any, **kwargs: Any) -> Any:
        if not _logged["once"]:
            log.warning(
                "tool_alias_used: legacy name '%s' resolves to '%s' — update your client config; aliases are removed in v1.2.",
                legacy_name,
                target_meta.name,
            )
            _logged["once"] = True
        return await wrapped_target(*args, **kwargs)

    alias.__wrapped__ = wrapped_target
    alias.__name__ = legacy_name
    return alias
