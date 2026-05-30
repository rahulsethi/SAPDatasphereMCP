# SAP Datasphere MCP Server
# File: policy_evidence.py
# Version: v1 (1.0)

"""Static disclosure data about the SAP API Policy v4/2026 posture.

Returned by :func:`policy.disclosure` and the
``datasphere_governance_api_policy_check`` MCP tool. The point is to provide
a single, citable, machine-readable snapshot of what this server claims about
its compliance posture.
"""

from __future__ import annotations

from typing import Any, Dict

__all__ = ["POLICY_VERSION", "POLICY_URL", "EVIDENCE"]

POLICY_VERSION = "v4.2026a"
POLICY_URL = "https://help.sap.com/doc/sap-api-policy/latest/en-US/API_Policy_latest.pdf"
POLICY_EFFECTIVE_DATE = "2026-06-09"

#: Recommended deployment posture in order from most defensible to least.
DEPLOYMENT_TIERS = [
    {
        "tier": "A",
        "name": "Behind SAP Integration Suite MCP Gateway",
        "summary": "Operators wrap this server behind the gateway; sanctioned metering, agent identity, audit, and rate limiting inherited from SAP.",
        "recommended_for": ["production", "customer-facing", "regulated environments"],
        "reference": "https://community.sap.com/t5/technology-blog-posts-by-sap/pov-3-using-integration-suite-as-your-governed-mcp-server-platform-part-3-4/ba-p/14328366",
    },
    {
        "tier": "B",
        "name": "Direct OAuth client_credentials",
        "summary": "Server hits Datasphere Consumption APIs directly with a technical user OAuth client.",
        "recommended_for": ["internal use", "development", "evaluation"],
        "reference": "https://community.sap.com/t5/technology-blog-posts-by-sap/using-technical-user-in-sap-datasphere-consumption-apis-client-credentials/ba-p/14218919",
    },
    {
        "tier": "C",
        "name": "mTLS-bound client_credentials via IAS",
        "summary": "Replace the client_secret with a certificate. Higher friction, higher assurance.",
        "recommended_for": ["security-conscious deployments"],
        "reference": "https://community.sap.com/t5/technology-blog-posts-by-sap/sap-btp-security-how-to-realize-client-credentials-flow-with-it-2-mtls/ba-p/13564508",
    },
]


EVIDENCE: Dict[str, Any] = {
    "policy_version": POLICY_VERSION,
    "policy_url": POLICY_URL,
    "policy_effective_date": POLICY_EFFECTIVE_DATE,
    "claims": [
        {
            "id": "read-only",
            "claim": "This server exposes no write tools targeting tenant administrative surfaces (no user CRUD, no schema mutation, no task chain triggering).",
            "verified_by": "tools.governance.api_policy_check returns empty 'gated' list; tools/_metadata.py declares risk_level=low for every tool.",
        },
        {
            "id": "documented-apis-only",
            "claim": "Consumes only SAP-documented Datasphere Catalog and Consumption APIs via OAuth 2.0 client_credentials (the technical-user pattern documented in help.sap.com).",
            "verified_by": "client.py uses /api/v1/datasphere/* (and legacy /api/v1/dwc/*) — no ODP-via-RFC, no scraped surfaces.",
        },
        {
            "id": "audit-log",
            "claim": "Structured JSONL audit log emitted per tool call when DATASPHERE_AUDIT_ENABLED=1. Argument values fingerprinted (never logged in plaintext); tenant URL hashed.",
            "verified_by": "audit.py:AuditLog.commit() schema.",
        },
        {
            "id": "redaction",
            "claim": "Redaction layer scrubs secrets/tokens from tool returns by default (DATASPHERE_REDACTION_ENABLED=1).",
            "verified_by": "redaction.py default patterns.",
        },
        {
            "id": "policy-gate",
            "claim": "DATASPHERE_API_POLICY_STRICT=1 refuses any tool flagged as policy-gated. v1.0 ships no gated tools; flag is reserved for future surfaces.",
            "verified_by": "policy.py:permits().",
        },
        {
            "id": "mtls-supported",
            "claim": "mTLS-bound client_credentials supported via DATASPHERE_OAUTH_MTLS_CERT / _KEY.",
            "verified_by": "auth.OAuthClient — see Architecture_v1.0.md §10.",
        },
        {
            "id": "deployment-recommendation",
            "claim": "Documentation recommends the SAP Integration Suite MCP Gateway as the preferred production deployment.",
            "verified_by": "public_docs/SAP_API_POLICY.md tier table.",
        },
    ],
    "deployment_tiers": DEPLOYMENT_TIERS,
    "disclosure_url": "https://github.com/rahulsethi/SAPDatasphereMCP/blob/main/public_docs/SAP_API_POLICY.md",
    "contact": "https://github.com/rahulsethi/SAPDatasphereMCP/issues",
}
