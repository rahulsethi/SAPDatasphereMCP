# Quickstart — five minutes to your first answer

This guide gets you from zero to "Claude is answering questions about my SAP Datasphere tenant" in five minutes.

---

## 1. Install

```bash
uvx mcp-sap-datasphere-server
```

That's it — `uvx` will fetch and run the latest version in an isolated environment. (Prefer `pip` or `npx`? See [INSTALLATION.md](./INSTALLATION.md).)

---

## 2. Set four environment variables

```bash
export DATASPHERE_TENANT_URL="https://my-tenant.eu10.hcs.cloud.sap"
export DATASPHERE_OAUTH_TOKEN_URL="https://my-tenant.authentication.eu10.hana.ondemand.com/oauth/token"
export DATASPHERE_CLIENT_ID="sb-xxxx"
export DATASPHERE_CLIENT_SECRET="yyyy"
```

(PowerShell users: see [INSTALLATION.md](./INSTALLATION.md#setting-them--powershell).)

**No tenant yet?** Skip this step and run with `DATASPHERE_MOCK_MODE=1` instead — you'll get realistic sample data so you can try every tool without touching a real environment.

---

## 3. Add to Claude Desktop

Open Claude Desktop → Settings → Developer → Edit Config, and add:

```json
{
  "mcpServers": {
    "sap-datasphere": {
      "command": "uvx",
      "args": ["mcp-sap-datasphere-server"]
    }
  }
}
```

If you set your env vars at the OS level, that's enough. Otherwise, include them under an `"env": { ... }` block inside the server entry (see [INSTALLATION.md](./INSTALLATION.md#wire-to-claude-desktop)).

---

## 4. Restart Claude Desktop

Fully quit and re-open it. You'll see the SAP Datasphere tools appear in the tool picker (the little hammer icon in the input box).

---

## 5. Try your first prompt

In a new Claude chat, ask:

> **Show me the spaces in my SAP Datasphere tenant.**

Claude will call `datasphere_catalog_list_spaces` and come back with something like:

> I found 4 spaces in your tenant: **HR_SPACE** (12 assets), **SALES_ANALYTICS** (47 assets), **FINANCE_REPORTING** (23 assets), and **SUPPLY_CHAIN** (31 assets). Would you like me to explore any of them?

---

## 6. Try a richer prompt — profile a dataset

Now try this:

> **Profile the EMPLOYEES asset in the HR_SPACE space.**

This triggers our built-in **`profile_dataset` Prompt** — a pre-built workflow that:

1. Pulls the schema for the asset
2. Counts rows
3. Computes per-column statistics (null ratio, distinct count, top values)
4. Returns it all as a tidy summary

Claude's response will read like a data quality report — column-by-column, with the highlights surfaced at the top. For an HR dataset you might see something like:

> **EMPLOYEES** (1,247 rows, 18 columns)
> - `employee_id` — 100% populated, 1,247 distinct (likely primary key)
> - `department` — 100% populated, 6 distinct values; top: *Engineering* (412), *Sales* (287)
> - `manager_id` — 96% populated, 89 distinct; 51 employees with no manager assigned
> - `hire_date` — earliest 2008-03-15, latest 2026-05-22
> ...

No SQL written. No query consoles opened. Just a question.

---

## Where to go next

- **Browse the full tool catalog** in [TOOLS.md](./TOOLS.md) — all 24 tools, grouped by category, with example return shapes.
- **Try the other built-in Prompts** — `audit_space`, `explain_analytical_model`, `compare_assets`, `find_data_about_topic`. See the [MCP Prompts section](./TOOLS.md#mcp-prompts) of TOOLS.md.
- **Use MCP Resources directly** — Claude (and other MCP clients) can read `datasphere://space/HR_SPACE` or `datasphere://asset/EMPLOYEES/sample` as first-class context. See the [MCP Resources section](./TOOLS.md#mcp-resources) of TOOLS.md.
- **Going to production?** Read [SAP_API_POLICY.md](../SAP_API_POLICY.md) for our recommended enterprise deployment posture.
