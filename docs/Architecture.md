<!-- SAP Datasphere MCP Server -->
<!-- File: Architecture.md -->
<!-- Version: v6 -->

# Architecture – SAP Datasphere MCP Server (v0.3)

This document describes the architecture of the **SAP Datasphere MCP Server** as of **v0.3.x**.

Design intent:

- **Read-only by default** (catalog + consumption-style querying).
- **LLM-friendly tools** with small, predictable JSON shapes.
- **Guardrails** (caps + truncation metadata) to keep LLM-driven exploration safe.
- **Plugin-ready** so future capabilities can be added without destabilizing core.

---

## High-level view

The server exposes SAP Datasphere as a set of MCP tools.

```text
MCP Host (Claude Desktop / IDE / agent)
        |
        | JSON-RPC (stdio) or HTTP (optional transport)
        v
+------------------------------+
|       Transport Layer        |
|  - stdio server              |
|  - http server (optional)    |
+--------------+---------------+
               |
               v
+------------------------------+
|        Tool Layer            |
|  sap_datasphere_mcp.tools     |
|  - tasks.py (core tools)      |
|  - plugins/* (optional tools) |
+--------------+---------------+
               |
               v
+------------------------------+
|      Client / Auth Layer     |
|  - config.py  (env config)   |
|  - auth.py    (OAuth2)       |
|  - client.py  (HTTP calls)   |
|  - cache.py   (TTL cache)    |
+--------------+---------------+
               |
               v
        SAP Datasphere APIs
        - Catalog APIs
        - Consumption (Relational)
        - Consumption (Analytical)
```

---

## Core modules & responsibilities

### `config.py` (DatasphereConfig)

- Loads configuration from environment variables.
- v0.3 adds:
  - TLS verification toggle
  - tool caps (preview/query/profile/analytical/search)
  - metadata cache settings

**Key env vars**
- `DATASPHERE_TENANT_URL`
- `DATASPHERE_OAUTH_TOKEN_URL`
- `DATASPHERE_CLIENT_ID`
- `DATASPHERE_CLIENT_SECRET`
- `DATASPHERE_VERIFY_TLS` (`1` default, `0` to disable in special cases)
- `DATASPHERE_MOCK_MODE` (`1` enables in-memory mock client)
- `DATASPHERE_MAX_ROWS_PREVIEW`, `DATASPHERE_MAX_ROWS_QUERY`, `DATASPHERE_MAX_ROWS_PROFILE`, `DATASPHERE_MAX_ROWS_ANALYTICAL`
- `DATASPHERE_MAX_SEARCH_RESULTS`
- `DATASPHERE_CACHE_TTL_SECONDS`, `DATASPHERE_CACHE_MAX_ENTRIES`
- `DATASPHERE_PLUGINS` (comma-separated plugin modules)

### `auth.py` (OAuthClient)

- Client-credentials flow (technical user).
- SAP-recommended HTTP Basic auth for token requests.
- In-memory token cache with refresh leeway.
- Respects `verify_tls` and `mock_mode`.

### `client.py` (DatasphereClient)

- Talks to SAP Datasphere endpoints (Catalog + Consumption).
- Returns structured models (spaces/assets/query results).
- Supports:
  - list spaces/assets
  - relational preview/query
  - analytical query
  - asset metadata retrieval
  - relational `$metadata` retrieval (EDMX/XML) where available

### `cache.py` (TTLCache)

- In-process TTL cache (metadata-focused).
- Used to reduce repeated calls for:
  - list spaces/assets
  - asset metadata
  - column listing
  - deterministic summaries

### `tools/tasks.py` (Core tools)

Single place where core tool business logic lives.

Responsibilities:
- clamp/cap all row-returning operations
- normalize meta blocks (`requested_*`, `effective_*`, `cap_*`, `cap_applied`)
- keep outputs small and JSON-friendly
- provide deterministic “summary” helpers (no free-form prose required)

### `plugins/registry.py` (Plugin loading)

- Loads plugin modules listed in `DATASPHERE_PLUGINS`.
- Each plugin module exposes `register_tools(server)`.
- Plugin failures are **non-fatal** (core server should still run).
- Plugin status is observable via:
  - `datasphere_plugins_status`
  - included in `datasphere_diagnostics` output

### Transports

- **stdio transport**: intended for MCP hosts (Claude Desktop, etc.).
- **http transport**: optional for local debugging / alternate clients.

Transports should remain thin:
- instantiate a server
- call `register_tools(server)` (core)
- load plugins via registry

---

## MCP tool catalog (as of v0.3)

All tool names below match the actual registered names in `tools/tasks.py`.

### Health, diagnostics, identity
- `datasphere_ping`
- `datasphere_diagnostics`
- `datasphere_get_tenant_info`
- `datasphere_get_current_user`
- `datasphere_plugins_status`

### Spaces & catalog
- `datasphere_list_spaces`
- `datasphere_list_assets`
- `datasphere_search_assets`
- `datasphere_space_summary`

### Asset metadata & schema/columns
- `datasphere_get_asset_metadata`
- `datasphere_list_columns`
- `datasphere_describe_asset_schema`

### Data access
- `datasphere_preview_asset`
- `datasphere_query_relational`
- `datasphere_query_analytical`

### Discovery & profiling
- `datasphere_find_assets_with_column`
- `datasphere_find_assets_by_column`
- `datasphere_profile_column`

### Deterministic summaries & comparison (v0.3)
- `datasphere_summarize_asset`
- `datasphere_summarize_space`
- `datasphere_summarize_column_profile`
- `datasphere_compare_assets_basic`

---

## Safety, limits & performance

Core safety principles:

- **Read-only**: no write/admin APIs.
- **Bounded queries**:
  - `top`/`limit` inputs are clamped to config caps.
  - tool outputs expose truncation clearly via `meta`.
- **Sampling over scanning**:
  - profiling and schema inference operate on sample rows.
- **Caching**:
  - TTL cache reduces repeated metadata calls.
- **Mock mode**:
  - `DATASPHERE_MOCK_MODE=1` swaps in an in-memory dataset.

---

## Typical flows

### Orient me in this tenant
1. `datasphere_diagnostics`
2. `datasphere_list_spaces`
3. `datasphere_summarize_space` (pick a space)
4. `datasphere_list_assets`
5. `datasphere_summarize_asset` (pick an asset)

### Find something by domain language
1. `datasphere_search_assets` (query like “invoice” / “employee”)
2. `datasphere_get_asset_metadata` (check relational/analytical support)
3. `datasphere_preview_asset` or `datasphere_query_relational`
4. optionally `datasphere_profile_column`

### Analytical query path
There is **no dedicated `datasphere_list_analytical_models` tool** in core v0.3.
Instead:
1. `datasphere_list_assets` (or `datasphere_search_assets`)
2. `datasphere_get_asset_metadata` to confirm `supports_analytical_queries=true`
3. `datasphere_query_analytical`

### Compare two assets quickly
1. `datasphere_compare_assets_basic`
2. optionally `datasphere_summarize_asset` for each side

---

## Notes & decisions (v0.3)

- Tool naming standard: **American spelling** in tool names (`summarize_*`), even if prose uses “summarise”.
- Analytical querying tool name is **`datasphere_query_analytical`** (no `_basic` suffix).
- Dedicated “list analytical models” is deferred; core uses `get_asset_metadata` to determine analytical capability.
- Plugin failures must not block core server startup; plugin status is exposed for observability.

---

## Version notes (summary)

- **v0.1.0**: baseline read-only tools (spaces/assets/preview/query/schema).
- **v0.2.0**: metadata tools + richer profiling + diagnostics + mock mode.
- **v0.3.0**: caps + TTL cache + analytical query tool + deterministic summary tools + asset comparison + plugin-ready architecture.
