# Migrating from v0.3.x to v1.0

SAP Datasphere MCP Server **1.0.0** ships on **2026-05-30** and consolidates three breaking changes — a distribution rename, a tool-naming overhaul, and a license change — into a single, coherent release. This guide walks you from any v0.3.x install to v1.0 in five steps or less.

> If you are still on v0.3.1 or earlier today, you have until at least **1.2 (~Q4 2026)** before legacy tool names stop resolving, and until **March 2027** before the legacy `/api/v1/dwc/*` API path tree disappears. There is no rush — but the longer you wait, the more compounds.

See also: [INSTALLATION.md](./INSTALLATION.md) · [TOOLS.md](./TOOLS.md) · [SAP_API_POLICY.md](./SAP_API_POLICY.md) · [COMMERCIAL_LICENSING.md](./COMMERCIAL_LICENSING.md)

---

## 1. What changed at a glance

- **PyPI package renamed** — `mcp-sap-datasphere-server` is gone; install `sap-datasphere-mcp` (matches the console script and the sibling `sap-bdc-mcp` package).
- **All 22 tools renamed** to a `datasphere_<category>_<verb>` shape; old names still work as aliases through 1.1 and are removed in 1.2 (~Q4 2026).
- **License changed** — v1.0+ is **PolyForm Noncommercial 1.0.0**. v0.3.x and earlier stay MIT. Non-commercial use is unchanged; commercial use needs a separate license — see [COMMERCIAL_LICENSING.md](./COMMERCIAL_LICENSING.md).

---

## 2. Step-by-step migration

### Step 1 — Uninstall the old package

```bash
pip uninstall mcp-sap-datasphere-server
```

The old package name is permanently retired on PyPI. There is no upgrade-in-place path — the new distribution is a different project.

### Step 2 — Install 1.0

Pick whichever matches your environment:

```bash
# PyPI (recommended for most users)
pip install sap-datasphere-mcp

# uvx (zero-install, run-on-demand)
uvx sap-datasphere-mcp

# npm (for hosts that prefer Node-style wiring)
npx -y @rahulsethi/sap-datasphere-mcp
```

All three resolve to the same FastMCP server. The console script name (`sap-datasphere-mcp`) is unchanged across distributions.

### Step 3 — Confirm Python 3.11+

```bash
python --version
# Python 3.11.x or newer
```

v1.0 raises the Python floor from 3.10 to 3.11 to match the sibling repo and unlock newer typing features. If you are on 3.10, upgrade your interpreter before reinstalling.

### Step 4 — Acknowledge the license change

- **Community, research, and personal use** are unchanged — PolyForm Noncommercial 1.0.0 is at least as permissive as MIT for those audiences. Just install and use it.
- **Internal enterprise evaluation / POC** is also fine under PolyForm — it explicitly permits non-commercial use, including pre-purchase evaluation at companies.
- **Commercial deployment** (paid consulting using the server, embedding it in a vendor product, or running it as part of a paid managed service) requires a commercial license. Path is short and friendly: see [COMMERCIAL_LICENSING.md](./COMMERCIAL_LICENSING.md).

### Step 5 — Update your Claude Desktop config

The `command` field does **not** change — the console script is still `sap-datasphere-mcp`. Only the install reference changes. A typical Claude Desktop config after upgrade looks like:

```json
{
  "mcpServers": {
    "sap-datasphere": {
      "command": "uvx",
      "args": ["sap-datasphere-mcp"],
      "env": {
        "DATASPHERE_TENANT_URL": "https://<your-tenant>.eu10.hcs.cloud.sap",
        "DATASPHERE_OAUTH_CLIENT_ID": "sb-...",
        "DATASPHERE_OAUTH_CLIENT_SECRET": "...",
        "DATASPHERE_OAUTH_TOKEN_URL": "https://<your-tenant>.authentication.eu10.hana.ondemand.com/oauth/token"
      }
    }
  }
}
```

**Restart Claude Desktop fully** after updating the config — Claude Desktop caches MCP tool catalogs at startup, so a half-restart will keep the old (now-gone) tool names visible until the cache invalidates.

---

## 3. Tool name changes

All 22 existing tools were renamed under a `datasphere_<category>_<verb>` scheme. Two brand-new governance tools were added on top, for a v1.0 total of **24 tools**.

Old names continue to resolve through 1.0 and 1.1 via a deprecation alias layer, with a one-time-per-process log line per alias call. Aliases are **removed in 1.2 (~Q4 2026)**.

| Category | Old name (v0.3.x) | New name (v1.0) |
|---|---|---|
| connectivity | `datasphere_ping` | `datasphere_connectivity_ping` |
| connectivity | `datasphere_diagnostics` | `datasphere_connectivity_diagnostics` |
| connectivity | `datasphere_get_tenant_info` | `datasphere_connectivity_tenant_info` |
| connectivity | `datasphere_get_current_user` | `datasphere_connectivity_whoami` |
| connectivity | `datasphere_plugins_status` | `datasphere_connectivity_plugins_status` |
| catalog | `datasphere_list_spaces` | `datasphere_catalog_list_spaces` |
| catalog | `datasphere_list_assets` | `datasphere_catalog_list_assets` |
| catalog | `datasphere_get_asset_metadata` | `datasphere_catalog_get_asset` |
| catalog | `datasphere_list_columns` | `datasphere_catalog_list_columns` |
| catalog | `datasphere_space_summary` | `datasphere_catalog_space_overview` |
| query | `datasphere_preview_asset` | `datasphere_query_preview` |
| query | `datasphere_query_relational` | `datasphere_query_relational` |
| query | `datasphere_query_analytical` | `datasphere_query_analytical` |
| discover | `datasphere_search_assets` | `datasphere_discover_assets` |
| discover | `datasphere_find_assets_with_column` | `datasphere_discover_assets_with_column` |
| discover | `datasphere_find_assets_by_column` | `datasphere_discover_assets_by_column` |
| profile | `datasphere_describe_asset_schema` | `datasphere_profile_schema` |
| profile | `datasphere_profile_column` | `datasphere_profile_column` |
| summarize | `datasphere_summarize_asset` | `datasphere_summarize_asset` |
| summarize | `datasphere_summarize_space` | `datasphere_summarize_space` |
| summarize | `datasphere_summarize_column_profile` | `datasphere_summarize_column_profile` |
| summarize | `datasphere_compare_assets_basic` | `datasphere_summarize_compare_assets` |
| governance | *(new in 1.0)* | `datasphere_governance_api_policy_check` |
| governance | *(new in 1.0)* | `datasphere_governance_audit_tail` |

If your agent or workflow hard-codes any old name, update it before 1.2 lands. Until then, you will see a structured deprecation log line in the server's stderr the first time each old name is called in a given process.

---

## 4. Environment variable additions

All new env vars are **optional** and default to **off**. v1.0 does not require any new mandatory configuration over v0.3.x.

| Variable | Purpose | Default |
|---|---|---|
| `DATASPHERE_API_PATH_LEGACY` | Force the legacy `/api/v1/dwc/*` path order (see Section 5). Useful escape hatch for tenants still on older waves. | `0` |
| `DATASPHERE_AUDIT_ENABLED` | Turn on the structured JSONL audit log of every tool call. | `0` |
| `DATASPHERE_AUDIT_LOG_PATH` | Override the audit log path. | `~/.cache/sap-datasphere-mcp/audit.log` |
| `DATASPHERE_API_POLICY_STRICT` | Refuse any tool flagged as `policy_class=gated`. No-op at 1.0 (no gated tools); reserved for future tools. | `0` |
| `DATASPHERE_REDACTION_ENABLED` | Scrub secrets, tokens, and JWTs from tool returns before serialization. **Recommended on.** | `1` |
| `DATASPHERE_OAUTH_MTLS_CERT` | Path to a client certificate for mTLS-bound `client_credentials` via SAP IAS (RFC 8705). | unset |
| `DATASPHERE_OAUTH_MTLS_KEY` | Path to the matching private key. Both `_CERT` and `_KEY` must be set together. | unset |
| `DATASPHERE_MCP_BEARER_TOKEN` | Required bearer token when running with the optional HTTP transport. Not used by the default stdio transport. | unset |
| `DATASPHERE_RESOURCE_SAMPLE_ROWS` | Row cap for the `datasphere://...asset/{name}/sample` MCP Resource. | `5` |

For the complete env var reference (including v0.3.x carryover vars like `DATASPHERE_TENANT_URL`, `DATASPHERE_VERIFY_TLS`, `DATASPHERE_MOCK_MODE`, `DATASPHERE_PLUGINS`), see [INSTALLATION.md](./INSTALLATION.md).

---

## 5. API path migration

SAP migrated the Datasphere REST surface in Wave 2025.19. v1.0 follows.

| v0.3.x default | v1.0 default |
|---|---|
| `GET /api/v1/dwc/catalog/spaces` | `GET /api/v1/datasphere/consumption/catalog/spaces` |
| `GET /api/v1/dwc/catalog/spaces/{space}/assets` | `GET /api/v1/datasphere/consumption/catalog/spaces/{space}/assets` |
| `GET /api/v1/dwc/consumption/relational/{space}/{asset}` | `GET /api/v1/datasphere/consumption/relational/{space}/{asset}` |
| `GET /api/v1/dwc/consumption/analytical/{space}/{asset}` | `GET /api/v1/datasphere/consumption/analytical/{space}/{asset}` |

The default path order is **flipped**: v1.0 hits the modern tree first and falls back to the legacy tree only if explicitly told to. If your tenant is on an older wave that does not yet expose the modern tree, set:

```bash
DATASPHERE_API_PATH_LEGACY=1
```

…to revert. SAP has committed to supporting the legacy `/api/v1/dwc/*` tree through **March 2027**, after which `DATASPHERE_API_PATH_LEGACY` becomes inert. We will cut a v2.0 that removes the toggle before that deadline.

You can confirm which tree the server is currently hitting via:

```text
datasphere_connectivity_diagnostics
# or
datasphere_governance_api_policy_check
```

Both surface a `path_mode` field (`"modern"` or `"legacy"`).

---

## 6. New things to discover

v1.0 is not just a rename — it adds first-in-class capabilities that no other SAP MCP server ships today.

- **Five MCP Prompts** — `profile_dataset`, `audit_space`, `explain_analytical_model`, `compare_assets`, `find_data_about_topic`. Pre-assembled multi-tool flows your client can offer as one-click recipes. See [TOOLS.md](./TOOLS.md).
- **Four MCP Resources** — URI-addressable catalog content under `datasphere://space/{id}/...`. Hosts that support MCP Resources can pre-load tenant context without ever calling a tool.
- **Two new governance tools** — `datasphere_governance_api_policy_check` (reports the current deployment posture, audit/redaction/mTLS status, and tool policy classification) and `datasphere_governance_audit_tail` (returns the last N audit log lines when audit is enabled).
- **MCP tool annotations** — every tool is now tagged `readOnlyHint=true`, `destructiveHint=false`. Claude Desktop and other hosts can skip confirmation prompts on tools that cannot mutate your tenant.
- **`outputSchema` + structured content** — every tool that returns structured data declares a JSON Schema, so your agent can reason over typed output instead of free-text scraping.
- **Cursor-based pagination** — `datasphere_catalog_list_spaces`, `datasphere_catalog_list_assets`, and the `datasphere_discover_*` family accept opaque cursors for large tenants.

The sibling [SAPBDCMCP](https://github.com/rahulsethi/SAPBDCMCP) project ships under the same naming conventions, same license model, and same governance posture. If you operate across Datasphere and BDC, install both and use them side-by-side in the same Claude Desktop session — your agent will not have to context-switch.

---

## 7. Breaking changes

| # | Change | Severity |
|---|---|---|
| B1 | PyPI package name `mcp-sap-datasphere-server` → `sap-datasphere-mcp` | **High** — every install command changes |
| B2 | All 22 tool names changed (aliases through 1.1, removed in 1.2) | **Medium** — aliases buy time; act before Q4 2026 |
| B3 | License MIT → PolyForm Noncommercial 1.0.0 (v1.0+ only; v0.3.x stays MIT) | **Medium for commercial users**, **none for everyone else** |
| B4 | Python floor 3.10 → 3.11 | **Low** — 3.11 has been GA since late 2022 |
| B5 | Default API path `/api/v1/dwc/*` → `/api/v1/datasphere/*` (legacy escape hatch available) | **Low** — auto-fallback via env var |
| B6 | Internal entry `tools.tasks.register_tools` removed; replaced by `tools.registry.register_all` | **Low** — only affects code importing internal APIs (none expected externally) |

---

## 8. Troubleshooting

**"I get `ImportError: No module named mcp_sap_datasphere_server` after upgrade."**
You uninstalled the old package but did not install the new one, or installed it into a different virtualenv. Run:

```bash
pip install sap-datasphere-mcp
python -c "import sap_datasphere_mcp; print(sap_datasphere_mcp.__version__)"
```

The version string should be `1.0.0` or newer.

**"Claude Desktop says my tool doesn't exist."**
Claude Desktop caches the MCP tool catalog at startup. After changing your config (or after the server's tool list changes), **fully quit Claude Desktop** (not just close the window — quit from the menu / system tray) and reopen. The new tool list will appear on next connection.

**"I get 404 on every catalog call after upgrading."**
Your tenant may still be on a Datasphere wave that only exposes the legacy `/api/v1/dwc/*` path tree. Confirm by setting:

```bash
DATASPHERE_API_PATH_LEGACY=1
```

…and trying again. If that fixes it, leave the env var set until your tenant rolls forward (SAP supports both paths through March 2027). If it does not fix it, the failure is elsewhere — check OAuth credentials and `datasphere_connectivity_diagnostics`.

**"My old `datasphere_list_spaces` tool call still works but I get a deprecation message."**
That is the alias layer working as designed — your call is being routed to the new `datasphere_catalog_list_spaces` implementation. Update your tool name reference at your convenience; aliases ship through 1.1 and are removed in 1.2.

**"Should I enable audit logging?"**
For personal exploration: optional. For enterprise / customer-environment deployments: **yes** — set `DATASPHERE_AUDIT_ENABLED=1` and review [SAP_API_POLICY.md](./SAP_API_POLICY.md) for the recommended deployment posture.

---

## 9. Get help

- **Issues & migration questions** — [github.com/rahulsethi/SAPDatasphereMCP/issues](https://github.com/rahulsethi/SAPDatasphereMCP/issues)
- **Discussions** — [github.com/rahulsethi/SAPDatasphereMCP/discussions](https://github.com/rahulsethi/SAPDatasphereMCP/discussions)
- **Commercial license inquiries** — see [COMMERCIAL_LICENSING.md](./COMMERCIAL_LICENSING.md)
- **API Policy posture & enterprise compliance** — see [SAP_API_POLICY.md](./SAP_API_POLICY.md)
