<!-- SAP Datasphere MCP Server -->
<!-- File: TestPrompts_v0.3.md -->
<!-- Version: v2 -->

# Test Prompts – SAP Datasphere MCP Server v0.3

This document collects example natural-language prompts to exercise each MCP tool exposed by the SAP Datasphere MCP Server as of **v0.3**.

Guidelines:
- Use these in Claude Desktop (or any MCP client).
- Replace placeholders like `YOUR_SPACE_ID` / `YOUR_ASSET_ID` / `YOUR_COLUMN` with values from your tenant.
- These prompts should also work in **mock mode** (`DATASPHERE_MOCK_MODE=1`) using:
  - Spaces: `MOCK_SALES`, `MOCK_FINANCE`
  - Assets: `SALES_ORDERS`, `CUSTOMERS`, `GL_BALANCES`

---

## Quick “smoke test” flow

1) “Run `datasphere_diagnostics`, then list spaces, then summarize the most interesting space.”  
2) “Pick one asset and run: metadata → list columns → preview 20 rows.”  
3) “Profile one numeric column and one id-like column.”  
4) “If the asset supports analytical queries, run a small analytical query too.”

---

## Health, diagnostics, identity

### `datasphere_ping`
- “Call `datasphere_ping` and show me the raw JSON.”
- “Check whether the Datasphere MCP backend is alive. Use ping and summarize the result in one sentence.”

### `datasphere_diagnostics`
- “Run `datasphere_diagnostics` and summarize any failing checks. Include whether we’re in mock mode.”
- “Call diagnostics and tell me: what’s configured, what’s working, and what looks misconfigured?”

### `datasphere_get_tenant_info`
- “Use `datasphere_get_tenant_info` to show the tenant host, region hint, TLS verify flag, and caps—no secrets.”
- “Show me the redacted tenant configuration and explain what each part implies.”

### `datasphere_get_current_user`
- “Call `datasphere_get_current_user` and explain whether you’re using mock mode or a real technical user.”
- “Who are you acting as when calling Datasphere APIs? Use the current-user tool and explain safely.”

---

## Spaces & catalog

### `datasphere_list_spaces`
- “List all spaces you can see with ids and descriptions. Highlight anything that looks like Sales or Finance.”
- “Call `datasphere_list_spaces` and tell me how many spaces exist, plus a short summary of each.”

### `datasphere_list_assets`
- “In the space `YOUR_SPACE_ID`, call `datasphere_list_assets` and show the first 15 assets with id, name, type, description.”
- “List assets in `YOUR_SPACE_ID` and group them by type (tables/views/models).”

### `datasphere_search_assets`
- “Search across all spaces for assets related to ‘employee’ and show me the top 10 matches.”
- “Within `YOUR_SPACE_ID`, search for assets matching ‘invoice’ and include space_id, type, and description.”

### `datasphere_space_summary`
- “Run `datasphere_space_summary` for `YOUR_SPACE_ID` and tell me what kinds of assets dominate that space.”
- “Summarize the space and suggest 2–3 candidate ‘core’ assets to start exploring.”

---

## Metadata & columns

### `datasphere_get_asset_metadata`
- “Call `datasphere_get_asset_metadata` for asset `YOUR_ASSET_ID` in `YOUR_SPACE_ID` and tell me whether it supports relational and/or analytical queries.”
- “Fetch asset metadata and highlight the most useful URLs/endpoints it exposes.”

### `datasphere_list_columns`
- “List columns for `YOUR_ASSET_ID` in `YOUR_SPACE_ID` and show types, nullability, and key flags if available.”
- “Call `datasphere_list_columns` and then propose which columns look like dimensions vs measures.”

### `datasphere_describe_asset_schema`
- “Use `datasphere_describe_asset_schema` on `YOUR_ASSET_ID` with top=25 and summarize column shapes and example values.”
- “Describe the schema from a sample and warn me if the sample is too small or truncated.”

---

## Data access

### `datasphere_preview_asset`
- “Preview 20 rows from `YOUR_ASSET_ID` in `YOUR_SPACE_ID`. Only select columns `COL_A, COL_B, COL_C`.”
- “Preview rows from `YOUR_ASSET_ID` sorted by `SOME_DATE desc`, and explain any truncation or caps shown in meta.”

### `datasphere_query_relational`
- “Query `YOUR_ASSET_ID` in `YOUR_SPACE_ID` with select=[…], filter=‘…’, order_by=‘…’, top=50, skip=0 and show the JSON.”
- “Run a relational query to fetch the latest 10 records (by a date column). Include the exact `$filter`/`$orderby` you used.”

### `datasphere_query_analytical`
- “Check metadata for `YOUR_ASSET_ID` first; if it supports analytical queries, run `datasphere_query_analytical` with top=25 and show the JSON.”
- “Run an analytical query with a small filter and order_by, and explain the meta block (requested vs effective).”

> Note: v0.3 core does not require a special ‘list analytical models’ tool. Use `datasphere_get_asset_metadata` to confirm analytical support.

---

## Column discovery & profiling

### `datasphere_find_assets_with_column`
- “In space `YOUR_SPACE_ID`, find assets that contain column name `YOUR_COLUMN` (exact match, case-insensitive).”
- “Use `datasphere_find_assets_with_column` for `YOUR_COLUMN` and suggest which matching asset is the best ‘primary source’.”

### `datasphere_find_assets_by_column`
- “Across all spaces, find assets that expose column `YOUR_COLUMN`. Respect limits and show stats about what was scanned.”
- “Find where `YOUR_COLUMN` exists across spaces, then pick one candidate asset and pull its metadata + a 10-row preview.”

### `datasphere_profile_column`
- “Profile column `YOUR_COLUMN` in `YOUR_ASSET_ID` with top=200. Show nulls, distincts, and any numeric/categorical summary.”
- “Profile a likely ID column and tell me whether it looks like a business key or just a low-cardinality code.”

---

## Deterministic summaries & comparison (v0.3)

### `datasphere_summarize_asset`
- “Summarize asset `YOUR_ASSET_ID` in `YOUR_SPACE_ID` and list suggested dimensions/measures plus any key columns.”
- “Call `datasphere_summarize_asset` and then recommend 2–3 follow-up queries you would run (relational or analytical).”

### `datasphere_summarize_space`
- “Summarize the space `YOUR_SPACE_ID`, show total assets, top types, and a small sample list.”
- “Use `datasphere_summarize_space` and then recommend which asset looks like the best ‘starting point’ for analysis.”

### `datasphere_summarize_column_profile`
- “Generate a deterministic summary for the profile of column `YOUR_COLUMN` in `YOUR_ASSET_ID` (null fraction, role hint, highlights).”
- “Use the summarize-column-profile tool and explain what the role hint implies for analytics.”

### `datasphere_compare_assets_basic`
- “Compare `ASSET_A` in `SPACE_A` vs `ASSET_B` in `SPACE_B`. Show common columns, differences, and join candidates.”
- “Compare two assets and tell me whether they look like the same entity at different grains.”

---

## Plugins (v0.3)

### `datasphere_plugins_status`
- “Call `datasphere_plugins_status` and show me which plugins are configured, loaded, or failing (with errors).”
- “If any plugins failed to load, summarize the failure reasons and suggest what to fix.”

---

## Multi-tool orchestration scenarios

### Tenant reconnaissance
> “Run diagnostics, list spaces, summarize the most interesting space, then pick one asset and do: metadata → list columns → preview 20 rows.”

### Analytical path discovery
> “Search for assets related to ‘sales’. For the top 3 matches, fetch metadata and identify which supports analytical queries. Run a small analytical query on the best candidate.”

### Data quality quick scan
> “Pick an asset with a date column and an amount column. Profile both columns, then summarize the column profiles and flag nulls/outliers.”

### Join hypothesis
> “Find assets containing column `CUSTOMER_ID`. Compare two likely candidates and propose a join strategy using join candidates.”

### Mock mode demo
> “Assume mock mode is enabled. Run diagnostics, list spaces/assets, preview `MOCK_SALES/SALES_ORDERS`, profile `AMOUNT`, and summarize the asset.”
