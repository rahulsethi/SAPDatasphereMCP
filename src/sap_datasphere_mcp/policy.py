# SAP Datasphere MCP Server
# File: policy.py
# Version: v1 (1.0)

"""SAP API Policy v4/2026 gating.

The policy module classifies tools into three buckets:

- ``permitted_always`` — always callable (connectivity + governance tools that
  surface posture, never tenant data).
- ``permitted_under_cc`` — callable under OAuth client_credentials. The whole
  read-only data surface lives here.
- ``gated`` — refused when ``DATASPHERE_API_POLICY_STRICT=1``. v1.0 ships no
  gated tools; this is reserved for future surfaces.

The gate is intentionally simple. Tools declare their ``policy_class`` via
``@tool_metadata`` in :mod:`sap_datasphere_mcp.tools._metadata`, and this
module reads from there.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from . import policy_evidence

__all__ = ["PolicyDecision", "is_strict", "permits", "disclosure"]


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def is_strict() -> bool:
    """Whether the policy gate is in strict mode."""
    return _env_flag("DATASPHERE_API_POLICY_STRICT", default=False)


@dataclass
class PolicyDecision:
    """Result of a permit check."""

    allowed: bool
    reason: str
    policy_class: str

    def as_error(self) -> Dict[str, Any]:
        return {
            "ok": False,
            "error": {
                "code": "policy_denied",
                "message": self.reason,
                "hint": "Set DATASPHERE_API_POLICY_STRICT=0 to allow, or deploy behind SAP Integration Suite MCP Gateway. See public_docs/SAP_API_POLICY.md.",
            },
            "meta": {
                "policy_version": policy_evidence.POLICY_VERSION,
                "policy_class": self.policy_class,
                "strict": True,
            },
        }


def permits(tool_name: str, *, policy_class: str, strict: Optional[bool] = None) -> PolicyDecision:
    """Decide whether ``tool_name`` may run given the current policy mode.

    Parameters
    ----------
    tool_name
        Canonical (v1.0) tool name.
    policy_class
        One of ``permitted_always``, ``permitted_under_cc``, ``gated``.
    strict
        Override the env-derived strict flag (useful for tests).
    """
    in_strict = is_strict() if strict is None else strict

    if policy_class == "permitted_always":
        return PolicyDecision(True, "Permitted unconditionally.", policy_class)
    if policy_class == "permitted_under_cc":
        return PolicyDecision(True, "Permitted under OAuth client_credentials.", policy_class)
    if policy_class == "gated":
        if in_strict:
            return PolicyDecision(
                False,
                f"Tool '{tool_name}' is policy-gated and DATASPHERE_API_POLICY_STRICT=1.",
                policy_class,
            )
        return PolicyDecision(True, "Gated tool permitted (strict mode off).", policy_class)
    return PolicyDecision(
        True,
        f"Unknown policy class '{policy_class}'; defaulting to allow.",
        policy_class or "unknown",
    )


def disclosure() -> Dict[str, Any]:
    """Return the deployment-time policy posture snapshot."""
    from .tools import _metadata as tool_metadata_module  # local import to avoid cycle

    tools_by_class: Dict[str, list] = {
        "permitted_always": [],
        "permitted_under_cc": [],
        "gated": [],
    }
    for name, meta in tool_metadata_module.iter_tools():
        bucket = meta.policy_class if meta.policy_class in tools_by_class else "permitted_always"
        tools_by_class[bucket].append(name)
    for k in tools_by_class:
        tools_by_class[k].sort()

    audit_enabled = _env_flag("DATASPHERE_AUDIT_ENABLED", default=False)
    redaction_enabled = _env_flag("DATASPHERE_REDACTION_ENABLED", default=True)
    mtls_enabled = bool(os.environ.get("DATASPHERE_OAUTH_MTLS_CERT") and os.environ.get("DATASPHERE_OAUTH_MTLS_KEY"))
    api_path_legacy = _env_flag("DATASPHERE_API_PATH_LEGACY", default=False)

    return {
        "policy_version": policy_evidence.POLICY_VERSION,
        "policy_url": policy_evidence.POLICY_URL,
        "policy_effective_date": policy_evidence.POLICY_EFFECTIVE_DATE,
        "deployment_posture": _deployment_posture(mtls_enabled, api_path_legacy),
        "recommended_path": "SAP Integration Suite MCP Gateway",
        "tools_by_class": tools_by_class,
        "audit_enabled": audit_enabled,
        "redaction_enabled": redaction_enabled,
        "mtls_enabled": mtls_enabled,
        "api_path_legacy": api_path_legacy,
        "strict": is_strict(),
        "disclosure_url": policy_evidence.EVIDENCE["disclosure_url"],
        "evidence": policy_evidence.EVIDENCE,
    }


def _deployment_posture(mtls: bool, legacy_paths: bool) -> str:
    if mtls:
        return "tier_c_mtls_client_credentials"
    if legacy_paths:
        return "tier_b_oauth_client_credentials_legacy_paths"
    return "tier_b_oauth_client_credentials"
