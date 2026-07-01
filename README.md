# SAP Datasphere MCP Server

> **v1.0.0** — Read-only. API Policy v4/2026 aligned. Sibling to [SAPBDCMCP](https://github.com/rahulsethi/SAPBDCMCP).

[![License: BSL 1.1](https://img.shields.io/badge/license-BSL%201.1-blue)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/mcp-sap-datasphere-server)](https://pypi.org/project/mcp-sap-datasphere-server/)
[![Python](https://img.shields.io/pypi/pyversions/mcp-sap-datasphere-server)](https://pypi.org/project/mcp-sap-datasphere-server/)
[![CI](https://github.com/rahulsethi/SAPDatasphereMCP/actions/workflows/ci.yml/badge.svg)](https://github.com/rahulsethi/SAPDatasphereMCP/actions/workflows/ci.yml)

An open-source [Model Context Protocol](https://modelcontextprotocol.io/) server that lets AI agents — Claude, Cursor, or any MCP-compatible client — safely explore an **SAP Datasphere** tenant. Discover spaces, list assets, preview rows, profile columns, search by column name, and summarize analytical models — all through a clean, read-only tool surface that respects SAP's API governance posture.

```text
MCP host (Claude Desktop, Cursor, ...)
        │
        ▼
sap-datasphere-mcp  ──>  FastMCP server  ──>  tools/registry  ──>  category facades
                                                                   │
                                                                   ▼
                                          DatasphereClient (httpx)  ──>  /api/v1/datasphere/* (modern)
                                                                   ──>  /api/v1/dwc/* (legacy fallback)
                                          policy / audit / redaction interceptor chain
```

---

## Highlights

- **24 read-only tools** across `connectivity`, `catalog`, `query`, `discover`, `profile`, `summarize`, `governance`.
- **5 MCP Prompts** and **4 MCP Resources** — first SAP MCP server to ship either.
- **SAP API Policy v4/2026 aligned** — documented posture, optional audit log, redaction layer, Integration Suite **MCP Gateway** as the recommended enterprise deployment path.
- **Sibling to [SAPBDCMCP](https://github.com/rahulsethi/SAPBDCMCP)** — same maintainer, same naming, same license model. Run them side-by-side in the same MCP host.
- **No write tools, ever.** Hard guarantee for the 1.x line.
- **OAuth 2.0 client_credentials** (HTTP Basic, with body fallback). mTLS-bound client_credentials via IAS is a documented **Tier C** posture on the roadmap.
- **stdio + streamable-HTTP** transports; optional bearer auth on HTTP.

---

## Install — pick one

```bash
# uv / uvx — fastest, no global install
uvx mcp-sap-datasphere-server

# pip / pipx
pip install mcp-sap-datasphere-server        # or:  pipx install mcp-sap-datasphere-server

# npm (npx-wrapper bootstraps the Python package via uvx)
npx -y @rahulsethi/sap-datasphere-mcp
```

> The **console script** is still `sap-datasphere-mcp` — that's what you run, wire into Claude Desktop, and put in MCP host configs. The PyPI *package name* is `mcp-sap-datasphere-server`.

Full install guide and Claude Desktop / Cursor wiring is in [`public_docs/INSTALLATION.md`](public_docs/INSTALLATION.md).

---

## Configure

Four env vars are required, the rest are optional. Copy [`.env.example`](.env.example) or `set-datasphere-env.example.ps1` to a local file and fill in:

```bash
export DATASPHERE_TENANT_URL=https://<your-tenant>.<region>.hcs.cloud.sap
export DATASPHERE_OAUTH_TOKEN_URL=https://<your-uaa>/oauth/token
export DATASPHERE_CLIENT_ID=<your-technical-client>
export DATASPHERE_CLIENT_SECRET=<your-client-secret>
```

Optional knobs you'll reach for most often:

| Env var | Purpose | Default |
|---|---|---|
| `DATASPHERE_MOCK_MODE` | Run in-memory; no real tenant. | `0` |
| `DATASPHERE_API_PATH_LEGACY` | Force legacy `/api/v1/dwc/*` first. | `0` |
| `DATASPHERE_AUDIT_ENABLED` | Write a JSONL audit log per tool call. | `0` |
| `DATASPHERE_OAUTH_MTLS_CERT` / `_KEY` | mTLS-bound client_credentials via IAS (Tier C). *Recognized and reported for posture; token-flow binding is on the roadmap, not yet wired in.* | unset |
| `DATASPHERE_MCP_BEARER_TOKEN` | Bearer auth for the HTTP transport. | unset |

Full env table: see [`public_docs/INSTALLATION.md`](public_docs/INSTALLATION.md).

---

## Quick start

```bash
sap-datasphere-mcp --version    # sap-datasphere-mcp 1.0.0
sap-datasphere-mcp              # starts the stdio MCP server
```

Then add this to your MCP host config (Claude Desktop / Cursor):

```json
{
  "mcpServers": {
    "sap-datasphere": {
      "command": "sap-datasphere-mcp",
      "args": [],
      "env": {
        "DATASPHERE_TENANT_URL": "https://...",
        "DATASPHERE_OAUTH_TOKEN_URL": "https://.../oauth/token",
        "DATASPHERE_CLIENT_ID": "...",
        "DATASPHERE_CLIENT_SECRET": "..."
      }
    }
  }
}
```

Try a first prompt: *"Show me the SAP Datasphere spaces in my tenant."*

A richer one: *"Profile the EMPLOYEES asset in the HR_SPACE space."* — this drives our `profile_dataset` MCP Prompt automatically.

---

## Tool catalog

24 tools organized as:

- **Connectivity (5)** — `ping`, `diagnostics`, `tenant_info`, `whoami`, `plugins_status`
- **Catalog (5)** — `list_spaces`, `list_assets`, `get_asset`, `list_columns`, `space_overview`
- **Query (3)** — `preview`, `relational`, `analytical`
- **Discover (3)** — `assets`, `assets_with_column`, `assets_by_column`
- **Profile (2)** — `schema`, `column`
- **Summarize (4)** — `asset`, `space`, `column_profile`, `compare_assets`
- **Governance (2)** — `api_policy_check`, `audit_tail`

Every tool is prefixed `datasphere_<category>_`. Every tool is `readOnly`; none are `destructive`. Full reference with args + return shapes: [`public_docs/TOOLS.md`](public_docs/TOOLS.md).

### MCP Prompts (first in the SAP ecosystem)

| Prompt | Args | What it does |
|---|---|---|
| `profile_dataset` | `space_id`, `asset_name` | Schema + sample + per-column profile + narrative summary |
| `audit_space` | `space_id` | Inventory & governance report for a space |
| `explain_analytical_model` | `space_id`, `asset_name` | Plain-English explanation of dimensions, measures, hierarchies |
| `compare_assets` | `space_a`, `asset_a`, `space_b`, `asset_b` | Structural comparison + relationship inference |
| `find_data_about_topic` | `topic`, optional `space_ids` | Multi-space discovery for an analytic question |

### MCP Resources

```
datasphere://space/{space_id}
datasphere://space/{space_id}/asset/{asset_name}
datasphere://space/{space_id}/asset/{asset_name}/schema
datasphere://space/{space_id}/asset/{asset_name}/sample
```

Let your MCP host pre-load context without a tool call.

---

## Architecture (high level)

The boot path is `transports/stdio_server.py` → `server.create_server()` → `tools.registry.register_all()` → category facade modules → the 22 async implementations in `tools/tasks.py`. Each tool call goes through a small interceptor chain: **policy gate → audit start → tool → redaction → audit commit**.

Full architecture details and decision log are in `public_docs/` — see the [quick links](public_docs/README.md).

---

## API Policy v4/2026 posture

This server consumes only **SAP-documented** Datasphere Catalog and Consumption APIs via OAuth 2.0 client_credentials (the technical-user pattern). It does not scrape, reverse-engineer, or proxy non-public APIs. It is **read-only by construction** — there are no write/admin tools and there will never be any in the 1.x line.

For production deployments, we recommend wrapping this server behind the **SAP Integration Suite MCP Gateway**, which inherits SAP-sanctioned metering, agent identity, audit, and rate limiting. See [`public_docs/SAP_API_POLICY.md`](public_docs/SAP_API_POLICY.md) for the full disclosure, the three-tier deployment guide, and the `datasphere_governance_api_policy_check` tool you can call to print the deployment's current posture.

---

## Family

**SAPBDCMCP** — the same maintainer ships a sibling MCP server for **SAP Business Data Cloud** at [https://github.com/rahulsethi/SAPBDCMCP](https://github.com/rahulsethi/SAPBDCMCP). Same naming conventions (`<product>_<category>_<verb>`), same license model, same read-only enterprise posture. If you operate across Datasphere and BDC, run them side-by-side in Claude Desktop and switch between them mid-conversation — neither your agent nor you have to context-switch.

A **2-for-1 family discount** is available on commercial licenses for both.

---

## Migration from v0.3.x

In short:

```bash
pip install --upgrade mcp-sap-datasphere-server
```

The PyPI distribution name is unchanged (`mcp-sap-datasphere-server`) — upgrade in place. The 22 old tool names continue to work through v1.1 as deprecation aliases. Update your Claude Desktop / Cursor configs to the new `datasphere_<category>_<verb>` names before v1.2 (~Q4 2026). Full guide with the rename table: [`public_docs/MIGRATION.md`](public_docs/MIGRATION.md).

---

## Versioning

Current: **1.0.0** — SemVer-stable through the 1.x line. Tool names, argument shapes, prompt names, and resource URIs are public contract.

Recent releases:

- **1.0.0** — *graduation*: family alignment, API path migration, governance layer, MCP prompts + resources, BSL 1.1 relicense. (This release.)
- **0.3.1** — *cleanup*: examples folder, dead code removal, docs reorg.
- **0.3.0** — analytical querying, deterministic summaries, TTL cache, configurable caps.
- **0.2.0** — metadata, discovery, profiling extensions, mock mode.
- **0.1.0** — initial GitHub release.

Full changelog: [`CHANGELOG.md`](CHANGELOG.md).

---

## License

**Business Source License 1.1** for v1.0+. Versions v0.3.1 and earlier remain MIT-licensed.
Converts automatically to Apache 2.0 on 2029-01-01.

- Personal, research, academic, and internal evaluation use: **free**.
- Commercial use (paid consulting, embedding in a vendor product, hosted SaaS): **requires a separate commercial license**.

The path is friendly and the terms are reasonable — see [`COMMERCIAL_LICENSING.md`](COMMERCIAL_LICENSING.md) for how to get one.

---

## Contributing

Contributions accepted under the same license. No CLA required. See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Issues / contact

- Bugs / feature requests: https://github.com/rahulsethi/SAPDatasphereMCP/issues
- Commercial licensing: open a [Discussion](https://github.com/rahulsethi/SAPDatasphereMCP/discussions) with title `[Commercial License Inquiry] <your-org>`.
