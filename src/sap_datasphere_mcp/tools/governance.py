# SAP Datasphere MCP Server
# File: tools/governance.py
# Version: v1 (1.0)

"""Governance tools.

Houses the two v1.0-new tools (``api_policy_check`` and ``audit_tail``) and
provides their BINDINGS for the registry.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict, List, Tuple

from .. import audit as audit_mod
from .. import policy
from ._metadata import TOOL_REGISTRY, ToolMetadata

__all__ = ["api_policy_check", "audit_tail", "BINDINGS"]


async def api_policy_check() -> Dict[str, Any]:
    """Return the SAP API Policy v4/2026 posture of this deployment.

    Returns a structured snapshot suitable for procurement / security review:
    policy version, deployment tier, audit/redaction state, tool classes,
    and the public disclosure URL.
    """
    return {
        "ok": True,
        **policy.disclosure(),
    }


async def audit_tail(limit: int = 50) -> Dict[str, Any]:
    """Return the last ``limit`` audit log records.

    Requires ``DATASPHERE_AUDIT_ENABLED=1``. Returns an empty list (with an
    informational ``meta.audit_enabled=false`` flag) when audit is disabled.

    Parameters
    ----------
    limit
        Maximum number of records to return (capped at 500).
    """
    capped_limit = max(1, min(int(limit), 500))
    log = audit_mod.get_audit_log()
    records = log.tail(limit=capped_limit) if log.enabled else []
    return {
        "ok": True,
        "records": records,
        "meta": {
            "audit_enabled": log.enabled,
            "audit_log_path": str(log.path),
            "requested_limit": int(limit),
            "effective_limit": capped_limit,
            "count": len(records),
        },
    }


BINDINGS: List[Tuple[ToolMetadata, Callable[..., Awaitable[Any]]]] = [
    (TOOL_REGISTRY["datasphere_governance_api_policy_check"], api_policy_check),
    (TOOL_REGISTRY["datasphere_governance_audit_tail"], audit_tail),
]
