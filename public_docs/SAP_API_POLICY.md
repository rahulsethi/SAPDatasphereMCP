# SAP API Policy v4/2026 — Disclosure & Posture

This document explains where SAP Datasphere MCP Server stands with respect to the **SAP API Policy v4/2026** (effective **2026-06-09**) and what enterprise operators should consider when deploying it. It is written for procurement and security reviewers as much as for engineers.

See also: [MIGRATION.md](./MIGRATION.md) · [COMMERCIAL_LICENSING.md](./COMMERCIAL_LICENSING.md) · [TOOLS.md](./TOOLS.md)

---

## 1. What is the SAP API Policy v4/2026?

On 2026-02-XX, SAP published an updated [API Policy (v.4.2026a, PDF)](https://help.sap.com/doc/sap-api-policy/latest/en-US/API_Policy_latest.pdf), effective **2026-06-09**. The clause that matters for MCP servers is **Section 2.2.2**, which restricts the use of SAP APIs in connection with autonomous or generative AI systems — specifically, AI systems that plan, select, or execute sequences of API calls — except through **SAP-endorsed pathways**.

In plain English: SAP wants AI agents talking to SAP systems via channels SAP has explicitly blessed (the Integration Suite MCP Gateway, Joule, native HANA MCP, and the BDC Data Products / Delta Sharing surface), rather than via arbitrary community-built connectors hitting raw OAuth-protected APIs. The policy has been criticized by **DSAG** (the German SAP user group) as anti-competitive and has drawn industry coverage; see [CIO.com](https://www.cio.com/article/4166172/dsag-criticizes-saps-new-api-policy.html). Enforcement clarity is expected to evolve over the next 18 months.

This server is built and operated under the assumption that operators will read this policy themselves, decide what their organization's risk appetite allows, and (where appropriate) deploy under the most defensible posture available.

---

## 2. Where this MCP server stands

SAP Datasphere MCP Server is built **exclusively on officially documented SAP Datasphere APIs**:

- The **Catalog API** (`/api/v1/datasphere/consumption/catalog/*`)
- The **Consumption APIs** for relational and analytical access (`/api/v1/datasphere/consumption/{relational,analytical}/*`)
- Authentication via **OAuth 2.0 client_credentials** — the [officially documented "technical user" pattern](https://community.sap.com/t5/technology-blog-posts-by-sap/using-technical-user-in-sap-datasphere-consumption-apis-client-credentials/ba-p/14218919) SAP itself blogs about as the recommended programmatic access pattern.

What this server **does not do**:

- It does **not** scrape Datasphere UI HTML or screen-scrape internal pages.
- It does **not** reverse-engineer undocumented endpoints.
- It does **not** proxy or wrap the ODP-via-RFC patch surface (the specific surface area Section 2.2.2 most directly targets).
- It does **not** expose any write, create, update, delete, or admin tool. There are zero mutation paths in the 1.x line.

The deployment pattern is the same one SAP's own blog posts describe as the supported way to integrate with Datasphere programmatically. We document this transparently so reviewers can make their own call.

---

## 3. Tool classification

Every v1.0 tool is assigned a `policy_class` value, exposed via `datasphere_governance_api_policy_check` at runtime and documented here at design time.

| `policy_class` | What it means | Tools |
|---|---|---|
| **`permitted_always`** | Pure-local diagnostics, governance reporting, or metadata calls that touch no tenant data. Considered acceptable under any deployment posture. | `datasphere_connectivity_ping`, `datasphere_connectivity_diagnostics`, `datasphere_connectivity_tenant_info`, `datasphere_connectivity_whoami`, `datasphere_connectivity_plugins_status`, `datasphere_governance_api_policy_check`, `datasphere_governance_audit_tail` |
| **`permitted_under_cc`** | Read-only catalog, query, discovery, profiling, and summarization tools. Operate under OAuth client_credentials against documented Datasphere APIs. Recommended deployment is the **Integration Suite MCP Gateway** path (Tier A below). | `datasphere_catalog_list_spaces`, `datasphere_catalog_list_assets`, `datasphere_catalog_get_asset`, `datasphere_catalog_list_columns`, `datasphere_catalog_space_overview`, `datasphere_query_preview`, `datasphere_query_relational`, `datasphere_query_analytical`, `datasphere_discover_assets`, `datasphere_discover_assets_with_column`, `datasphere_discover_assets_by_column`, `datasphere_profile_schema`, `datasphere_profile_column`, `datasphere_summarize_asset`, `datasphere_summarize_space`, `datasphere_summarize_column_profile`, `datasphere_summarize_compare_assets` |
| **`gated`** | Tools refused under `DATASPHERE_API_POLICY_STRICT=1`. **None at 1.0.** Reserved for future tools that might touch sensitive surfaces. | *(empty in v1.0)* |

All 24 v1.0 tools are explicitly `readOnlyHint=true` and `destructiveHint=false` via MCP tool annotations.

---

## 4. Recommended deployment posture

Three tiers, in increasing order of defensibility:

### Tier A (most defensible) — Behind SAP Integration Suite MCP Gateway

Operators wrap this server behind the **[SAP Integration Suite MCP Gateway](https://community.sap.com/t5/technology-blog-posts-by-sap/pov-3-using-integration-suite-as-your-governed-mcp-server-platform-part-3-4/ba-p/14328366)** and expose only the gateway's `/mcp` endpoint upstream to agents.

Why this is the strongest posture:

- SAP-sanctioned **agent identity**, **metering**, **audit**, and **rate-limiting** are inherited from the gateway.
- The agent never holds OAuth client_credentials directly; the gateway brokers them.
- This is the path SAP itself recommends in its 2026 blog series.
- Procurement reviewers tend to accept gateway-mediated deployments without further escalation.

Recommended for: production deployments at SAP customers, multi-tenant SaaS embedding this server, anything customer-facing.

### Tier B (community / dev) — Direct OAuth client_credentials

What most early adopters will start with: the server runs locally (or in your org's network) and authenticates directly to your Datasphere tenant via OAuth 2.0 client_credentials. This is the pattern documented in every Datasphere MCP quick-start, including ours.

Recommended for: personal exploration, single-developer use against your own org's tenant, time-bounded evaluation or POC, dev/test tenants. **Not recommended** for production customer-facing workloads — Tier A is.

### Tier C (hardening) — mTLS-bound client_credentials via IAS

For Tier B deployments that want stronger client authentication, the roadmap adds **mTLS-bound client_credentials** via SAP IAS (RFC 8705), configured with:

```bash
DATASPHERE_OAUTH_MTLS_CERT=/path/to/client.crt
DATASPHERE_OAUTH_MTLS_KEY=/path/to/client.key
```

This replaces the OAuth `client_secret` with a certificate, eliminating shared-secret rotation as a failure mode and giving the IdP cryptographic proof of which client is connecting. See the SAP Community post [Realize client_credentials flow with IAS mTLS](https://community.sap.com/t5/technology-blog-posts-by-sap/sap-btp-security-how-to-realize-client-credentials-flow-with-it-2-mtls/ba-p/13564508).

> **Status: roadmap, not yet implemented.** `DATASPHERE_OAUTH_MTLS_CERT` / `_KEY` are recognized and reported by `datasphere_governance_api_policy_check` for posture disclosure, but the certificate binding is **not yet wired into the OAuth token flow** in `auth.py`. Do not rely on Tier C for enforcement today — use Tier A (MCP Gateway) or rotate the `client_secret` (Tier B) until it lands.

Recommended for (once implemented): any production-grade Tier B that cannot move to Tier A yet, and as defense-in-depth on top of Tier A.

---

## 5. What the server does to comply

Every v1.0 release ships the following compliance machinery on by default or one env var away from on:

- **Read-only by hard guarantee.** There are no write, admin, or destructive tools. This is a project-level guarantee for the entire 1.x line, not a config flag. Section 2.2.2's "execute sequences of API calls" concern is materially weakened when the API surface itself cannot mutate state.
- **Structured JSONL audit log** when enabled via `DATASPHERE_AUDIT_ENABLED=1`. Every tool call is logged with: tool name, duration, outcome, an **args fingerprint** (sha256 — argument values are never logged in plaintext), rows returned, a tenant URL hash, the OAuth subject, and the policy mode at the time. Default path `~/.cache/sap-datasphere-mcp/audit.log`, overridable via `DATASPHERE_AUDIT_LOG_PATH`.
- **Redaction layer** on by default (`DATASPHERE_REDACTION_ENABLED=1`). Regex-based scrubbing of OAuth client secrets, JWTs, bearer headers, and other obvious credential shapes before tool returns are serialized to the agent.
- **`datasphere_governance_api_policy_check` tool** — agents (or human operators) can ask the server itself for its current posture. Returns the policy version, deployment posture, recommended path, full tools-by-class classification, audit / redaction / mTLS flags, and a link to this document.
- **`datasphere_governance_audit_tail` tool** — when audit is enabled, returns the last N audit log lines. Useful for in-conversation compliance review.
- **Policy strict mode** — `DATASPHERE_API_POLICY_STRICT=1` refuses any tool tagged `policy_class=gated`. With the v1.0 surface this is a no-op (no gated tools), but the gate is wired so any future tool addition inherits the protection — operators who turn it on today get a forward-compatible safety net.
- **MCP tool annotations** — every tool advertises `readOnlyHint=true` and `destructiveHint=false`. Hosts that respect these annotations (Claude Desktop, Cursor) can adapt their confirmation UX accordingly.

---

## 6. What operators should do

If you are deploying this server in any environment more sensitive than your laptop:

1. **Audit the deployment against your own org's policy.** This document is best-effort transparency, not legal sign-off. Your org's procurement, security, and SAP-licensing teams have the final word.
2. **Consider the Integration Suite MCP Gateway** (Tier A) for production. It is the single biggest reduction in compliance risk available to you and SAP itself is steering customers there.
3. **Rotate OAuth `client_secret` values quarterly** at minimum. mTLS-bound client_credentials (Tier C) is on the roadmap (see the Tier C note above); until it lands, `client_secret` rotation is your Tier B control.
4. **Enable audit logging** — `DATASPHERE_AUDIT_ENABLED=1`. Reviewing the audit tail periodically is the simplest evidence-of-control your security team can ask for.
5. **Set `DATASPHERE_API_POLICY_STRICT=1`** as a defense-in-depth flag. It costs nothing today and protects you from future tool additions that might touch sensitive surfaces.
6. **Restrict outbound network access** from the MCP server host to only your Datasphere tenant and IdP. The server has no other legitimate destinations.

---

## 7. DSAG concerns and outlook

DSAG, the German-speaking SAP user group, has publicly criticized Section 2.2.2 as overly restrictive and anti-competitive — see [CIO.com](https://www.cio.com/article/4166172/dsag-criticizes-saps-new-api-policy.html) and [The Register](https://www.theregister.com/2026/04/29/new_sap_api_policy_provokes/). SAP has not yet published detailed enforcement guidance, and the gap between **policy** and **technical enforcement** is, at the time of writing, substantial. The June 9 effective date is policy-only; SAP's own June 9 security patch targets a narrower, unrelated surface (ODP-via-RFC), not OAuth client_credentials access to Datasphere consumption APIs.

We expect clarification over the next 12-18 months. This server is structured so that, if enforcement tightens, operators have a short, well-documented path to migrate: move to Tier A (Integration Suite MCP Gateway in front of this server) without losing any tooling.

**This is not legal advice.** It is engineering disclosure of the project's posture and the publicly available context as we understand it. Your legal counsel and SAP account team are the authoritative source for what your organization can and cannot do.

---

## 8. Contact for compliance questions

- **General questions / posture clarifications** — open a GitHub Issue at [github.com/rahulsethi/SAPDatasphereMCP/issues](https://github.com/rahulsethi/SAPDatasphereMCP/issues). Compliance-tagged issues are prioritized.
- **Procurement / commercial-license inquiries** — see [COMMERCIAL_LICENSING.md](./COMMERCIAL_LICENSING.md).
- **Security disclosures** — if you believe you have found a security issue, please use the security advisory path on the GitHub repo rather than a public issue.

---

## Sources

- SAP API Policy v.4.2026a — [help.sap.com/doc/sap-api-policy/latest/en-US/API_Policy_latest.pdf](https://help.sap.com/doc/sap-api-policy/latest/en-US/API_Policy_latest.pdf)
- DSAG critiques SAP's new API policy — [cio.com/article/4166172/dsag-criticizes-saps-new-api-policy.html](https://www.cio.com/article/4166172/dsag-criticizes-saps-new-api-policy.html)
- POV 3: Using Integration Suite as your governed MCP server platform — [community.sap.com](https://community.sap.com/t5/technology-blog-posts-by-sap/pov-3-using-integration-suite-as-your-governed-mcp-server-platform-part-3-4/ba-p/14328366)
- Using Technical User in Datasphere Consumption APIs (client_credentials) — [community.sap.com](https://community.sap.com/t5/technology-blog-posts-by-sap/using-technical-user-in-sap-datasphere-consumption-apis-client-credentials/ba-p/14218919)
- SAP BTP Security: client_credentials with IAS mTLS — [community.sap.com](https://community.sap.com/t5/technology-blog-posts-by-sap/sap-btp-security-how-to-realize-client-credentials-flow-with-it-2-mtls/ba-p/13564508)
- New SAP API policy provokes industry pushback — [theregister.com](https://www.theregister.com/2026/04/29/new_sap_api_policy_provokes/)
