# Tools, Prompts & Resources

The complete user-facing catalog for SAP Datasphere MCP Server **1.0.0**.

- **24 tools** across 7 categories
- **5 MCP Prompts** for reusable workflows
- **4 MCP Resource** URI patterns

Every tool is **read-only**. There are no write, update, delete, or import operations anywhere in the 1.x line.

New to the server? Start with [QUICKSTART.md](./QUICKSTART.md), then come back here. Not installed yet? See [INSTALLATION.md](./INSTALLATION.md).

> **Renaming note.** Tool names follow a `datasphere_<category>_<verb>` convention in 1.0. If you used 0.3.x, the old name is shown *in italics* next to each tool. Upgrading? See [MIGRATION.md](../MIGRATION.md).

---

## Connectivity (5 tools)

Tools that check the wire — is the tenant reachable, who am I, what's working.

### `datasphere_connectivity_ping` *(was `datasphere_ping`)*
A lightweight health check. Returns `ok` if the server can reach your tenant.

- **Args:** none
- **Read-only:** yes

```json
{ "status": "ok", "latency_ms": 142, "tenant": "my-tenant.eu10.hcs.cloud.sap" }
```

### `datasphere_connectivity_diagnostics` *(was `datasphere_diagnostics`)*
A deeper self-check. Reports on auth, TLS, configured env, and plugin state. Use this first when something feels off.

- **Args:** none
- **Read-only:** yes

```json
{
  "auth": "ok",
  "tls_verify": true,
  "mock_mode": false,
  "warnings": []
}
```

### `datasphere_connectivity_tenant_info` *(was `datasphere_get_tenant_info`)*
Identifies the tenant — region, type, version markers.

- **Args:** none
- **Read-only:** yes

### `datasphere_connectivity_whoami` *(was `datasphere_get_current_user`)*
Reports the identity the OAuth client maps to — useful for audit clarity.

- **Args:** none
- **Read-only:** yes

```json
{ "client_id": "sb-xxxx", "principal": "datasphere-readonly", "scopes": ["read"] }
```

### `datasphere_connectivity_plugins_status` *(was `datasphere_plugins_status`)*
Lists which optional plugins are loaded. (See [plugins docs](../docs/v1.0/PLUGINS.md) if you're authoring one.)

- **Args:** none
- **Read-only:** yes

---

## Catalog (5 tools)

Browse the structure of your tenant: spaces, assets, columns, metadata.

### `datasphere_catalog_list_spaces` *(was `datasphere_list_spaces`)*
Lists every space the OAuth client can see.

- **Args:** none
- **Read-only:** yes

```json
[
  { "id": "HR_SPACE", "name": "HR Analytics", "asset_count": 12 },
  { "id": "SALES_ANALYTICS", "name": "Sales", "asset_count": 47 }
]
```

### `datasphere_catalog_list_assets` *(was `datasphere_list_assets`)*
Lists assets in a given space — tables, views, analytical models.

- **Args:** `space_id` (string)
- **Read-only:** yes

```json
[
  { "name": "EMPLOYEES", "type": "table", "rows_estimate": 1247 },
  { "name": "HEADCOUNT_MODEL", "type": "analytical_model" }
]
```

### `datasphere_catalog_get_asset` *(was `datasphere_get_asset_metadata`)*
Full metadata for one asset — type, owner, description, tags, last-modified timestamps.

- **Args:** `space_id` (string), `asset_name` (string)
- **Read-only:** yes

### `datasphere_catalog_list_columns` *(was `datasphere_list_columns`)*
Lists column names and types for a given asset.

- **Args:** `space_id` (string), `asset_name` (string)
- **Read-only:** yes

```json
[
  { "name": "employee_id", "type": "INTEGER", "nullable": false },
  { "name": "hire_date", "type": "DATE", "nullable": true }
]
```

### `datasphere_catalog_space_overview` *(was `datasphere_space_summary`)*
A one-shot summary of a space — asset counts by type, recently-modified items, basic health.

- **Args:** `space_id` (string)
- **Read-only:** yes

---

## Query (3 tools)

Safe, parameterized reads. No SQL strings handed to the server — the tool builds the right query for you.

### `datasphere_query_preview` *(was `datasphere_preview_asset`)*
Returns the first N rows of an asset.

- **Args:** `space_id` (string), `asset_name` (string), `limit` (integer, default 10)
- **Read-only:** yes

```json
{
  "columns": ["employee_id", "name", "department"],
  "rows": [
    [1, "Ada Lovelace", "Engineering"],
    [2, "Grace Hopper", "Engineering"]
  ]
}
```

### `datasphere_query_relational`
Filtered/projected read against a relational asset (table or view). Bring `where` and `select` as structured arguments.

- **Args:** `space_id` (string), `asset_name` (string), `select` (list of strings, optional), `where` (object, optional), `limit` (integer, optional)
- **Read-only:** yes

### `datasphere_query_analytical`
Aggregated read against an analytical model. Specify measures and dimensions instead of writing OLAP queries by hand.

- **Args:** `space_id` (string), `model_name` (string), `measures` (list of strings), `dimensions` (list of strings, optional), `filters` (object, optional)
- **Read-only:** yes

```json
{
  "dimensions": ["department"],
  "measures": ["headcount"],
  "rows": [
    { "department": "Engineering", "headcount": 412 },
    { "department": "Sales", "headcount": 287 }
  ]
}
```

---

## Discover (3 tools)

Find things across the tenant — by name, by column, by column type.

### `datasphere_discover_assets` *(was `datasphere_search_assets`)*
Free-text search across asset names and descriptions.

- **Args:** `query` (string), `space_id` (string, optional)
- **Read-only:** yes

### `datasphere_discover_assets_with_column` *(was `datasphere_find_assets_with_column`)*
Find every asset that contains a column with the given name. Great for tracing where `customer_id` lives.

- **Args:** `column_name` (string), `space_id` (string, optional)
- **Read-only:** yes

```json
[
  { "space_id": "SALES_ANALYTICS", "asset": "ORDERS", "column": "customer_id" },
  { "space_id": "FINANCE_REPORTING", "asset": "INVOICES", "column": "customer_id" }
]
```

### `datasphere_discover_assets_by_column` *(was `datasphere_find_assets_by_column`)*
Find assets that have *any* column matching a pattern — partial names, type filter, or both. Slightly broader than `_with_column`.

- **Args:** `pattern` (string), `data_type` (string, optional), `space_id` (string, optional)
- **Read-only:** yes

---

## Profile (2 tools)

Compute quality and shape statistics over an asset's data — without writing the queries yourself.

### `datasphere_profile_schema` *(was `datasphere_describe_asset_schema`)*
Schema-only profile: column names, types, nullability, declared keys, declared semantic types. No data scan.

- **Args:** `space_id` (string), `asset_name` (string)
- **Read-only:** yes

### `datasphere_profile_column`
Data-level statistics for a single column: null ratio, distinct count, min/max, top-K values.

- **Args:** `space_id` (string), `asset_name` (string), `column_name` (string), `top_k` (integer, optional, default 5)
- **Read-only:** yes

```json
{
  "column": "department",
  "null_ratio": 0.0,
  "distinct_count": 6,
  "top_values": [
    { "value": "Engineering", "count": 412 },
    { "value": "Sales", "count": 287 }
  ]
}
```

---

## Summarize (4 tools)

Compact, human-readable rollups designed for direct inclusion in an LLM context window.

### `datasphere_summarize_asset`
A natural-language-friendly summary of one asset: type, purpose (if described), key columns, row scale, freshness.

- **Args:** `space_id` (string), `asset_name` (string)
- **Read-only:** yes

### `datasphere_summarize_space`
Same idea, one level up: what this space is about, what kinds of assets it holds, who owns it.

- **Args:** `space_id` (string)
- **Read-only:** yes

### `datasphere_summarize_column_profile`
Takes the output of `datasphere_profile_column` and turns it into a sentence: *"`department` is fully populated with 6 distinct values; the dominant value is Engineering (33%)."*

- **Args:** `space_id` (string), `asset_name` (string), `column_name` (string)
- **Read-only:** yes

### `datasphere_summarize_compare_assets` *(was `datasphere_compare_assets_basic`)*
Side-by-side comparison of two assets — overlapping columns, type mismatches, row-scale differences.

- **Args:** `space_id_a` (string), `asset_a` (string), `space_id_b` (string), `asset_b` (string)
- **Read-only:** yes

```json
{
  "common_columns": ["customer_id", "order_date"],
  "only_in_a": ["discount"],
  "only_in_b": ["tax_amount"],
  "type_mismatches": []
}
```

---

## Governance (2 tools)

New in 1.0 — the API Policy v4/2026 family.

### `datasphere_governance_api_policy_check` *(NEW)*
Reports the server's API Policy posture: what endpoints it uses, whether it's behind a Gateway, whether anything is using a deprecated path. Use this before going to production. See [SAP_API_POLICY.md](../SAP_API_POLICY.md) for what the fields mean.

- **Args:** none
- **Read-only:** yes

```json
{
  "policy_version": "v4/2026",
  "gateway_recommended": true,
  "legacy_paths_in_use": false,
  "warnings": []
}
```

### `datasphere_governance_audit_tail` *(NEW)*
Returns the most recent N entries from the local audit log (only available when `DATASPHERE_AUDIT_ENABLED=1`). Useful for showing an auditor exactly what your agent did.

- **Args:** `limit` (integer, optional, default 50)
- **Read-only:** yes

```json
[
  {
    "ts": "2026-05-30T10:14:22Z",
    "tool": "datasphere_catalog_list_spaces",
    "principal": "sb-xxxx",
    "outcome": "ok"
  }
]
```

---

## MCP Prompts

Reusable, parameterized prompts your client can offer as one-click workflows. (Claude Desktop and Cursor both surface these in their prompt pickers.)

| Prompt | Arguments | What it does |
|---|---|---|
| `profile_dataset` | `space_id`, `asset_name` | Schema + row count + per-column statistics, returned as a tidy data-quality report. |
| `audit_space` | `space_id` | Walks every asset in a space and produces an inventory with freshness, owner, and column counts. |
| `explain_analytical_model` | `space_id`, `model_name` | Plain-English explanation of what an analytical model measures, what its dimensions are, and how it's typically used. |
| `compare_assets` | `space_id_a`, `asset_a`, `space_id_b`, `asset_b` | Side-by-side narrative comparison — columns, types, overlaps, drift. |
| `find_data_about_topic` | `topic` (string) | Searches across spaces and columns for assets relevant to a topic ("customer churn", "revenue by region") and returns the best candidates. |

---

## MCP Resources

URI patterns the server exposes as first-class MCP Resources. Your client can read these directly without an explicit tool call — useful for pasting tenant context into a chat or attaching a sample to a model's input.

| URI pattern | What you get |
|---|---|
| `datasphere://space/{id}` | A summary document for a space — name, asset count, asset list, owner. |
| `datasphere://asset/{name}` | A summary document for an asset — type, columns, row scale, last modified. |
| `datasphere://asset/{name}/schema` | The asset's full schema (column names, types, nullability, keys) as a structured resource. |
| `datasphere://asset/{name}/sample` | A small row sample for the asset, formatted for easy reading. |

> Tip: in Claude Desktop, you can `@`-mention a resource by URI to pull it into the conversation as context. Combined with the Prompts above, this is the fastest way to give an agent everything it needs to reason about a piece of your tenant.

---

## See also

- [QUICKSTART.md](./QUICKSTART.md) — try your first tool in five minutes
- [INSTALLATION.md](./INSTALLATION.md) — install and wire to your MCP client
- [README.md](./README.md) — what this server is and who it's for
- [MIGRATION.md](../MIGRATION.md) — moving from 0.3.x to 1.0
- [SAP_API_POLICY.md](../SAP_API_POLICY.md) — the API Policy v4/2026 posture
