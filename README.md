<!-- SAP Datasphere MCP Server -->
<!-- File: README.md -->
<!-- Version: v2-public -->

# SAP Datasphere MCP Server

An experimental [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server that lets AI agents talk to **SAP Datasphere**.

The server exposes a small, focused set of **read-only** tools for:

- discovering spaces and assets,
- previewing data,
- describing schema,
- running simple relational queries, and
- basic search / profiling helpers.

Current status: **v0.1.0 – proof of concept / early preview**.  
APIs may still change in future versions.

---

## ✨ Features (v0.1.0)

All features are **read-only** against your Datasphere tenant.

### Health & connectivity

- `datasphere_ping`  
  Check that configuration & OAuth are at least sane.  
  TLS verification can be relaxed for corporate proxies (`DATASPHERE_VERIFY_TLS=0`).

### Spaces & catalog

- `datasphere_list_spaces`  
  List visible Datasphere spaces.

- `datasphere_list_assets`  
  List catalog assets (tables/views/models) in a given space.

### Data preview & querying

- `datasphere_preview_asset`  
  Fetch a small sample of rows from a relational asset.

- `datasphere_query_relational`  
  Run simple OData-style relational queries with:

  - `$select`
  - `$filter`
  - `$orderby`
  - `$top`
  - `$skip`

### Schema & profiling

- `datasphere_describe_asset_schema`  
  Sample-based column summary: names, example values, rough type inference, and simple null counts.

- `datasphere_profile_column`  
  Quick profile for a single column: sample size, null count, distinct count, basic numeric stats (min / max / mean).

### Search & summaries

- `datasphere_search_assets`  
  Fuzzy search assets by name / id across spaces.

- `datasphere_space_summary`  
  Small overview of a space: asset counts by type + a sample list of assets.

There are also a few **demo scripts** for local smoke-testing without an MCP client.

---

## 🧱 Architecture (high level)

Very roughly:

```text
MCP client (e.g. Claude Desktop)
        │
        ▼
MCP stdio transport  ──>  FastMCP server  ──>  tools/tasks.py (MCP tools)
                                               │
                                               ▼
                                         DatasphereClient
                                               │
                                               ▼
                            SAP Datasphere REST APIs (Catalog & Consumption)
```

- The `sap-datasphere-mcp` console script starts a stdio MCP server.
- `tools/tasks.py` defines all MCP tools and wires them to `DatasphereClient`.
- `DatasphereClient` wraps the Datasphere Catalog & Consumption APIs using `httpx`
  and returns simple JSON-serialisable structures.

---

## ✅ Requirements

- Python **3.10+** (developed and tested on 3.14).
- A working **SAP Datasphere** tenant.
- A **technical OAuth client** with:
  - token URL,
  - client ID,
  - client secret,
  - permission to call the Catalog & Consumption APIs.

This project is aimed at technical users who are comfortable with:

- environment variables,
- basic command-line usage, and
- SAP Datasphere / SAP BTP concepts.

---

## 🚀 Installation

### Option 1 – Install directly from GitHub (recommended for users)

In any virtual environment where you want to use the MCP server:

```bash
pip install "git+https://github.com/rahulsethi/SAPDatasphereMCP.git"
```

This installs:

- the `sap_datasphere_mcp` package,
- the `sap-datasphere-mcp` console script, and
- the required dependencies (`mcp`, `httpx`, `pydantic`, …).

### Option 2 – Clone the repo (recommended for contributors)

```bash
git clone https://github.com/rahulsethi/SAPDatasphereMCP.git
cd SAPDatasphereMCP

# Create and activate a virtualenv

# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# macOS / Linux (bash/zsh)
python -m venv .venv
source .venv/bin/activate

# Install in editable (dev) mode
pip install -e ".[dev]"
```

This gives you the same console script plus dev tools like `pytest` for local tests.

---

## ⚙️ Configure SAP Datasphere credentials

The MCP server reads its configuration from environment variables via
`DatasphereConfig.from_env()`.

At minimum you need:

- `DATASPHERE_TENANT_URL`  
  Base URL of your Datasphere tenant  
  e.g. `https://your-tenant-id.eu10.hcs.cloud.sap`

- `DATASPHERE_OAUTH_TOKEN_URL`  
  OAuth token endpoint for your technical client  
  e.g. `https://your-uaa-domain/oauth/token`

- `DATASPHERE_OAUTH_CLIENT_ID`  
  Client ID of your technical OAuth client.

- `DATASPHERE_OAUTH_CLIENT_SECRET`  
  Client secret of your technical OAuth client.

Optional:

- `DATASPHERE_VERIFY_TLS`  
  - `"1"` or unset: verify TLS certificates (default, recommended).  
  - `"0"`: **disable** TLS verification (only if you’re behind a corporate proxy
    with self-signed certs and you understand the risks).

### Example (PowerShell helper script, Windows)

Create `set-datasphere-env.ps1` in the project root:

```powershell
$env:DATASPHERE_TENANT_URL          = "https://your-tenant-id.eu10.hcs.cloud.sap"
$env:DATASPHERE_OAUTH_TOKEN_URL     = "https://your-uaa-domain/oauth/token"
$env:DATASPHERE_OAUTH_CLIENT_ID     = "your-client-id"
$env:DATASPHERE_OAUTH_CLIENT_SECRET = "your-client-secret"

# Optional: skip TLS verification for self-signed corporate proxies
# (only if you understand the security implications)
# $env:DATASPHERE_VERIFY_TLS = "0"

Write-Host "Datasphere environment variables set."
```

Then in each new shell:

```powershell
.\set-datasphere-env.ps1
```

On macOS / Linux you can do the same with an `export`-based shell script.

---

## 🧪 Local smoke tests

With env vars set and your virtualenv active:

```bash
pytest
```

Then try the demo scripts:

```bash
# List spaces via MCP tasks
python demo_mcp_list_spaces.py

# List assets in a specific space (set DATASPHERE_TEST_SPACE first)
python demo_mcp_list_assets.py

# Preview data (with optional filter)
python demo_mcp_preview_filtered.py

# Describe schema from a sample
python demo_mcp_describe_asset.py

# Query with filter/sort/select/skip
python demo_mcp_query_relational.py

# Search assets by name / id
python demo_mcp_search_assets.py

# Summarise a space
python demo_mcp_space_summary.py

# Profile one column
python demo_mcp_profile_column.py
```

Each script prints JSON-like results so you can see exactly what MCP tools
return to an AI agent.

---

## 🖥️ Running the MCP server

To start the stdio MCP server:

```bash
sap-datasphere-mcp
```

The process will listen on stdin/stdout using JSON-RPC as defined by MCP.  
You normally don’t talk to this directly; an MCP-compatible client
(e.g. Claude Desktop) launches it and sends requests over stdio.

---

## 🤖 Using with Claude Desktop (example)

Exact config file locations differ by OS and Claude version;  
check Anthropic’s docs for current paths.

Conceptually, you add an entry under `mcpServers` telling Claude how to start
your server and what env vars to pass.

Example `mcpServers` entry (JSON, comments removed):

```json
{
  "mcpServers": {
    "sap-datasphere": {
      "command": "sap-datasphere-mcp",
      "args": [],
      "env": {
        "DATASPHERE_TENANT_URL": "https://your-tenant-id.eu10.hcs.cloud.sap",
        "DATASPHERE_OAUTH_TOKEN_URL": "https://your-uaa-domain/oauth/token",
        "DATASPHERE_CLIENT_ID": "your-client-id",
        "DATASPHERE_CLIENT_SECRET": "your-client-secret",
        "DATASPHERE_VERIFY_TLS": "1"
      }
    }
  }
}
```

After editing the config, restart Claude Desktop.  
The new MCP server should appear in the list of tools the model can call.

---

## 🔧 MCP tools – details

All tools live in `sap_datasphere_mcp.tools.tasks` and are registered on the
MCP server under the names below.

### Health & discovery

- `datasphere_ping()` → `{ "ok": bool }`  
  Sanity check that config + OAuth at least look healthy.

- `datasphere_list_spaces()` →  
  `{ "spaces": [ { "id", "name", "description" }, ... ] }`

- `datasphere_list_assets(space_id)` →  
  `{ "space_id": str, "assets": [ { "id", "name", "type", "space_id", "description" }, ... ] }`

### Data preview & schema

- `datasphere_preview_asset(space_id, asset_name, top=20, select=None, filter=None, order_by=None)`  

  Returns:

  ```json
  {
    "columns": ["EMP_ID", "FIRST_NAME", "..."],
    "rows": [[101, "Rudransh", "..."], "..."],
    "truncated": false,
    "meta": {
      "space_id": "...",
      "asset_name": "...",
      "row_count": 3,
      "top": 20
    }
  }
  ```

- `datasphere_describe_asset_schema(space_id, asset_name, top=20)`  

  Uses a preview sample to infer basic column metadata:
  example values, rough types, and sample-based null counts.

- `datasphere_profile_column(space_id, asset_name, column, top=100)`  

  Builds a quick profile from sample rows:

  - inferred type list (e.g. `["int"]`),
  - sample size,
  - null count,
  - distinct count,
  - for numeric columns: min, max, mean,
  - example values.

### Relational querying

- `datasphere_query_relational(space_id, asset_name, select=None, filter=None, order_by=None, top=100, skip=0)`  

  Same result shape as `datasphere_preview_asset`, but exposes
  `$select`, `$filter`, `$orderby`, `$top`, `$skip`.

  This is intentionally simple; complex analytical / OLAP use-cases are out of
  scope for v0.1.

### Search & summaries

- `datasphere_search_assets(query, space_id=None, limit=50)`  

  Case-insensitive substring search on asset id / name across one or all spaces.

- `datasphere_space_summary(space_id, max_assets=50)`  

  Returns aggregate counts by asset type and a small sample asset list.

---

## 🗺️ Roadmap (future ideas)

These are **not** implemented yet, but are on the wish-list:

- Analytical / cube-style query helpers for analytical models.
- Explicit asset metadata + column list tools.
- “Find assets by column name” across spaces.
- Richer data profiling (histograms, categorical distributions, etc.).
- Better error classification and human-friendly error messages.
- Optional caching to reduce repeated calls to the same assets.
- Additional transports (e.g. HTTP) if needed by other MCP clients.

---

## 📦 Versioning

- **0.1.0** – first public preview (current)  
  Basic connectivity, catalog, preview, schema, query, search & profiling tools.  
  Tested against a small sample dataset (`EMP_View_Test`) in a single tenant/space.  

Expect breaking changes in the 0.x series as the API evolves.

---

## 📄 License

This project is released under the **MIT License**.  
See the `LICENSE` file for details.

You are free to use, modify, and redistribute the code, provided you keep the
copyright notice and license text in derivative works.
