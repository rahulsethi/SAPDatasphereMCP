# SAP Datasphere MCP Server

**SAP Datasphere MCP Server** lets Claude — or any MCP-compatible AI agent — safely explore your SAP Datasphere tenant in plain English. Ask about your spaces, profile a dataset, search for assets by column name, or have an agent summarize an analytical model — all through a single, read-only connector that speaks the Model Context Protocol.

> Read-only. API Policy v4/2026 aligned. Sibling to [SAPBDCMCP](https://github.com/rahulsethi/SAPBDCMCP).

---

## Quick links

- [INSTALLATION.md](./INSTALLATION.md) — install and wire to Claude Desktop / Cursor
- [QUICKSTART.md](./QUICKSTART.md) — five-minute getting started
- [TOOLS.md](./TOOLS.md) — all 24 tools, 5 prompts, 4 resources
- [MIGRATION.md](./MIGRATION.md) — upgrading from 0.3.x to 1.0
- [SAP_API_POLICY.md](./SAP_API_POLICY.md) — our API Policy v4/2026 posture
- [COMMERCIAL_LICENSING.md](./COMMERCIAL_LICENSING.md) — using this at work

---

## What it does

- **Talks to your SAP Datasphere tenant** over its OAuth-protected APIs and exposes it as a clean set of MCP tools.
- **Lists spaces, assets, columns, and metadata** so an AI agent can map your tenant before doing anything else.
- **Runs safe, parameterized queries** against relational and analytical objects — preview rows, filter, aggregate, no SQL string-pasting.
- **Profiles datasets** — row counts, null ratios, distinct counts, top values per column — without you having to write a single query.
- **Searches and discovers** assets by name, by column, or by column type across spaces.
- **Ships ready-made AI Prompts** like *profile_dataset*, *audit_space*, and *explain_analytical_model* so you (or your agent) don't start from a blank page.

Everything is read-only. There are no `create_`, `update_`, `delete_`, `write_`, or `import_` tools, and there never will be in the 1.x line.

---

## Who it's for

- **Data engineers** who want an AI co-pilot for tenant exploration, lineage hunts, and ad-hoc profiling.
- **Analytics consultants** doing discovery on customer Datasphere tenants where time-to-insight matters and write access is off the table.
- **AI builders** assembling agentic workflows over enterprise data and looking for a production-grade, governance-respecting connector.
- **SAP customers in pilot programs** evaluating how MCP and generative AI fit into their data stack — without compromising their environment.

---

## Why it's not "yet another data MCP"

- **Read-only by design.** Hard guarantee, not a flag. Suitable for production tenants and customer environments under change control.
- **First SAP MCP server to ship Prompts and Resources.** Most MCP servers expose tools only. We expose all three primitives the MCP spec defines, so your client can offer reusable workflows out of the box.
- **SAP API Policy v4/2026 aligned.** We document our posture, expose a `governance_api_policy_check` tool, and recommend the Integration Suite **MCP Gateway** path for enterprise deployments.
- **Part of the BDC family.** Same maintainer, same conventions, same license model as the SAP Business Data Cloud MCP server. Learn one, you know both.

---

## The family

SAP Datasphere MCP Server has a sibling: **[SAPBDCMCP](https://github.com/rahulsethi/SAPBDCMCP)**, the SAP Business Data Cloud MCP server. Same maintainer, same naming conventions, same license model, same read-only enterprise posture. If you operate across Datasphere and BDC, you can run both side-by-side in Claude Desktop and switch between them mid-conversation — your agent doesn't have to context-switch, and neither do you.

---

## Status

**Production-ready 1.0.** SemVer-stable through the 1.x line — tool names, argument shapes, prompt names, and resource URIs are public contract and won't change in a backwards-incompatible way until 2.0.

- **Version:** 1.0.0
- **Python:** 3.11+
- **Distribution:** PyPI `mcp-sap-datasphere-server`, npm `@rahulsethi/sap-datasphere-mcp`, uvx `uvx mcp-sap-datasphere-server`
- **Console script:** `sap-datasphere-mcp`

---

## License

Distributed under the **PolyForm Noncommercial 1.0.0** license — free for personal, community, research, and evaluation use. Commercial use (using this inside a paid engagement, a commercial product, or a revenue-generating workflow) requires a separate commercial license. The path is friendly and the terms are reasonable — see [COMMERCIAL_LICENSING.md](./COMMERCIAL_LICENSING.md).
