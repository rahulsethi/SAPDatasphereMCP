<!-- SAP Datasphere MCP Server -->
<!-- File: README.md -->
<!-- Version: v4-public -->

# SAP Datasphere MCP Server

An experimental [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server that lets AI agents talk to **SAP Datasphere**.

The server exposes a small, focused set of **read-only** tools to:

- Discover spaces and catalog assets
- Preview relational data
- Describe schemas from samples
- Run simple relational queries
- Search for assets and columns across spaces
- Profile columns with LLM-friendly summaries
- Inspect metadata & diagnostics to understand “what is this thing?”

**Current status: `v0.2.0` – Metadata & Diagnostics expansion (still preview).**  
APIs may still change in future versions.

The planned **PyPI distribution name** is:

- `mcp-sap-datasphere-server`  
  (See installation section – PyPI install will work once the package is actually published.)

---

## ✨ What’s new in v0.2.0 (on top of v0.1.0)

v0.1.0 gave you the basics: spaces, asset listings, previews, simple relational queries, search, and a lightweight column profile.

v0.2.0 focuses on **metadata, discovery, and better signals for LLMs**:

- **Richer catalog metadata** *(added in v0.2.0)*  
  - `datasphere_get_asset_metadata` – one place to get labels, type, descriptions, and which APIs (relational/analytical) are exposed for an asset.

- **Column-level introspection** *(added in v0.2.0)*  
  - `datasphere_list_columns` – lists columns using `$metadata` when possible (types, key flags, nullability) with a preview-based fallback.

- **Column search across spaces** *(added in v0.2.0)*  
  - `datasphere_find_assets_with_column` – scan one space for assets with a given column.  
  - `datasphere_find_assets_by_column` – scan multiple spaces with safety caps (max spaces / assets per space).

- **Richer profiling for a single column** *(extended in v0.2.0)*  
  - `datasphere_profile_column` now includes:
    - counts & distincts,
    - numeric stats: min, max, mean, **p25/p50/p75**, IQR, fences, outlier count,
    - **categorical summary** for low-cardinality columns (top values & fractions),
    - a coarse **`role_hint`** (`"id"`, `"measure"`, `"dimension"`) to help LLMs reason about semantics.

- **Diagnostics & identity helpers** *(added in v0.2.0)*  
  - Additional tools to inspect MCP & environment configuration, report mock/live mode, and expose “who am I talking to?” style information in a structured way.  
    (Handy when your AI is debugging connection issues.)

- **Mock mode for demos** *(added in v0.2.0)*  
  - `DATASPHERE_MOCK_MODE=1` switches the client to a small in-memory demo dataset so you can try tools without a real tenant.

Everything remains **read-only** against your Datasphere tenant.

---

## 🚦 Feature overview (v0.2.0)

This section describes the overall capabilities as of **v0.2.0**  
(see the dedicated v0.1.0 section below for the original baseline).

All tools live in `sap_datasphere_mcp.tools.tasks` and are exposed via the MCP server.

### 1. Health & connectivity

- Quick health check that configuration and OAuth are at least not obviously broken.
- TLS verification can be relaxed for gnarly corporate proxies using `DATASPHERE_VERIFY_TLS=0` (only if you know what you’re doing).
- Diagnostics tools provide a more structured view over configuration & connectivity (new in v0.2.0).

### 2. Spaces & catalog

- List SAP Datasphere spaces visible to the OAuth client.
- List catalog assets (tables/views/models) within a given space, including type and description.
- New in v0.2.0: **asset-level metadata**, including which APIs (relational / analytical) are available and useful URLs.

### 3. Data preview & relational queries

- Fetch small samples of rows from relational assets, with:
  - column list,
  - rows,
  - `truncated` flag,
  - a `meta` block carrying context (space, asset, query parameters).
- Run simple relational queries via the Consumption API:
  - `$select`, `$filter`, `$orderby`, `$top`, `$skip`.
- Stays firmly in **simple relational consumption**; OLAP/analytical models are intentionally out of scope for now.

### 4. Schema & column profiling

- Describe an asset’s schema from a sample:
  - column names,
  - rough Python types,
  - null counts,
  - example values.
- Profile a single column with:
  - counts & distincts,
  - numeric summary,
  - categorical summary (v0.2.0),
  - heuristic `role_hint` (v0.2.0).

### 5. Metadata & discovery

- Search assets by partial name / id / description / type across one or many spaces.
- Summarise a space:
  - total asset count,
  - counts by type,
  - small sample list of assets.
- New in v0.2.0:
  - list explicit columns using relational `$metadata`,
  - find assets by column name within a space or across spaces.

### 6. Diagnostics & identity (v0.2.0 additions)

v0.2.0 introduces helper tools to:

- surface environment & config details in a structured way,
- check mock/live mode and connection health from within an MCP client,
- expose basic “identity” context (technical user / mock vs real) that the agent can log or reason about.

These tools are intentionally simple and designed to be safe to call from LLMs.

---

## ✨ Features (v0.1.0)

This section reflects the **original feature set introduced in v0.1.0**.  
All of these remain available in v0.2.0.

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
- A working **SAP Datasphere** tenant (unless you run in mock mode).
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

### Option 1 – Install from PyPI *(once published)*

Planned distribution name:

```bash
pip install mcp-sap-datasphere-server
```

> The project is already configured with this name in `pyproject.toml`.  
> Until the package is actually published to PyPI, use the GitHub or source install options below.

### Option 2 – Install directly from GitHub *(recommended for now)*

In any virtual environment where you want to use the MCP server:

```bash
pip install "git+https://github.com/rahulsethi/SAPDatasphereMCP.git"
```

This installs:

- the `sap_datasphere_mcp` package,
- the `sap-datasphere-mcp` console script, and
- the required dependencies (`mcp`, `httpx`, `pydantic`, …).

### Option 3 – Clone the repo (recommended for contributors)

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

- `DATASPHERE_CLIENT_ID`  
  Client ID of your technical OAuth client.

- `DATASPHERE_CLIENT_SECRET`  
  Client secret of your technical OAuth client.

Optional:

- `DATASPHERE_VERIFY_TLS`  
  - `"1"` or unset: verify TLS certificates (default, recommended).  
  - `"0"`: **disable** TLS verification (only if you’re behind a corporate proxy
    with self-signed certs and you understand the risks).

- `DATASPHERE_MOCK_MODE` *(added in v0.2.0)*  
  - `"1"`: use an in-memory mock Datasphere client with a tiny demo dataset.  
  - `"0"` or unset: connect to the real Datasphere tenant using the OAuth details above.

### Example (PowerShell helper script, Windows)

Create `set-datasphere-env.ps1` in the project root:

```powershell
$env:DATASPHERE_TENANT_URL          = "https://your-tenant-id.eu10.hcs.cloud.sap"
$env:DATASPHERE_OAUTH_TOKEN_URL     = "https://your-uaa-domain/oauth/token"
$env:DATASPHERE_CLIENT_ID           = "your-client-id"
$env:DATASPHERE_CLIENT_SECRET       = "your-client-secret"

# Optional: skip TLS verification for self-signed corporate proxies
# (only if you understand the security implications)
# $env:DATASPHERE_VERIFY_TLS = "0"

# Optional: run in mock mode without a real tenant (v0.2.0)
# $env:DATASPHERE_MOCK_MODE = "1"

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

If `DATASPHERE_MOCK_MODE=1` is set, the server will run entirely in-memory
against a small demo dataset (v0.2.0).

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

## 🔧 MCP tools – quick reference (with version tags)

All tools live in `sap_datasphere_mcp.tools.tasks` and are registered on the
MCP server under the names below.

### Health & discovery

- `datasphere_ping` *(since v0.1.0)*  
  Basic connectivity check – returns `{ "ok": bool }`.

- `datasphere_diagnostics` *(added in v0.2.0)*  
  Runs a small set of health checks (client init, ping, list_spaces) and returns
  a structured diagnostics report including mock/live mode and elapsed time.

- `datasphere_get_tenant_info` *(added in v0.2.0)*  
  Redacted snapshot of tenant configuration (URLs, region hint, TLS settings, OAuth presence) – never returns secrets.

- `datasphere_get_current_user` *(added in v0.2.0)*  
  Describes the current Datasphere identity context (technical user vs mock mode) in a safe, high-level way.

### Spaces & catalog

- `datasphere_list_spaces` *(since v0.1.0)*  
  List visible Datasphere spaces.

- `datasphere_list_assets` *(since v0.1.0)*  
  List catalog assets in a given space (id, name, type, description).

- `datasphere_get_asset_metadata` *(added in v0.2.0)*  
  Fetch catalog metadata for a single asset: ids, name, label, description, type,
  relational/analytical exposure flags, useful URLs, plus raw payload.

### Data preview & querying

- `datasphere_preview_asset` *(since v0.1.0)*  
  Fetch a small sample of rows from an asset:
  - `columns`, `rows`, `truncated`, `meta`.

- `datasphere_query_relational` *(since v0.1.0)*  
  Relational query helper with:
  - `$select`, `$filter`, `$orderby`, `$top`, `$skip` reflected in `meta`.

### Schema & profiling

- `datasphere_describe_asset_schema` *(since v0.1.0)*  
  Infer column-oriented schema from a sample: column names, rough Python types,
  null counts, example values.

- `datasphere_list_columns` *(added in v0.2.0)*  
  List columns via relational `$metadata` (EDMX/XML) when available, falling back
  to preview-based inference. Includes type, key flag, nullability where possible.

- `datasphere_profile_column`  
  - *(v0.1.0)* basic profile: sample size, null count, distinct count, min, max, mean for numeric columns.  
  - *(extended in v0.2.0)* adds:
    - percentiles (p25, p50, p75),
    - IQR and outlier fences,
    - outlier count,
    - categorical summary for low-cardinality columns,
    - `role_hint` (`"id"`, `"measure"`, `"dimension"`).

### Search & summaries

- `datasphere_search_assets` *(since v0.1.0)*  
  Substring search on asset id, name, description, or type across one or many spaces.

- `datasphere_space_summary` *(since v0.1.0)*  
  Overview of a space: total assets, counts by type, sample list of assets.

- `datasphere_find_assets_with_column` *(added in v0.2.0)*  
  Within a single space, scan up to `max_assets` to find assets that expose a
  given column name (case-insensitive, exact match).

- `datasphere_find_assets_by_column` *(added in v0.2.0)*  
  Similar to the above, but across multiple spaces with caps on:
  - number of spaces scanned,
  - assets per space,
  - total matches returned (`limit`).

---

### Example response shape (preview)

A typical `datasphere_preview_asset` response looks like:

```json
{
  "columns": ["EMP_ID", "FIRST_NAME", "LAST_NAME"],
  "rows": [
    [101, "Rudransh", "Sharma"],
    [102, "Anita", "Müller"]
  ],
  "truncated": false,
  "meta": {
    "space_id": "HR_SPACE",
    "asset_name": "EMP_VIEW_TEST",
    "top": 20
  }
}
```

All other tools follow a similar pattern: small, predictable JSON structures that
are easy for LLMs (and humans) to reason about.

---

## 🗺️ Roadmap (future ideas)

These are **not** implemented yet, but are on the wish-list:

- Analytical / cube-style query helpers for analytical models.
- Higher-level RAG helpers (text embeddings + vector search on specific assets).
- More advanced data-quality checks.
- Better error classification and human-friendly error messages.
- Optional caching to reduce repeated calls to the same assets.
- Additional transports (e.g. HTTP) if needed by other MCP clients.

---

## 📦 Versioning

- **0.2.0 – metadata & diagnostics (current)**  
  - Catalog metadata tool (`datasphere_get_asset_metadata`)  
  - Column list & column search across spaces  
  - Richer column profiling (percentiles, IQR, outlier hints, role hints)  
  - Diagnostics & identity helpers; mock-mode support  
  - Packaging metadata prepared for distribution as `mcp-sap-datasphere-server` on PyPI

- **0.1.0 – first public preview**  
  - Basic connectivity, catalog, preview, schema, query, search & profiling tools.  
  - Tested against a small sample dataset (`EMP_View_Test`) in a single tenant/space.

Expect breaking changes in the **0.x** series as the API evolves.

---

## 📄 License

This project is released under the **MIT License**.  
See the `LICENSE` file for details.

You are free to use, modify, and redistribute the code, provided you keep the
copyright notice and license text in derivative works.
