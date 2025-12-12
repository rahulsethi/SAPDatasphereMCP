# SAP Datasphere MCP Server

An experimental [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server that lets AI agents talk to **SAP Datasphere**.

The server exposes a small, focused set of read-only tools for:

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

- **Health & connectivity**
  - `datasphere_ping` – check that configuration & OAuth work.
  - TLS verification can be relaxed for corporate proxies (`DATASPHERE_VERIFY_TLS=0`).

- **Spaces & catalog**
  - `datasphere_list_spaces` – list visible spaces.
  - `datasphere_list_assets` – list assets in a space.

- **Data preview & querying**
  - `datasphere_preview_asset` – fetch a small sample of rows from an asset.
  - `datasphere_query_relational` – run simple OData-style relational queries with:
    - `$select`, `$filter`, `$orderby`, `$top`, `$skip`.

- **Schema & profiling**
  - `datasphere_describe_asset_schema` – sample-based column summary
    (names + example values; basic type inference).
  - `datasphere_profile_column` – quick profile for a single column
    (null count, distinct count, simple numeric stats).

- **Search & summaries**
  - `datasphere_search_assets` – fuzzy search assets by name/id across spaces.
  - `datasphere_space_summary` – small overview of a space
    (asset counts by type + sample assets).

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



---The sap-datasphere-mcp console script starts a stdio MCP server.

---tools/tasks.py defines all the MCP tools and wires them to DatasphereClient.

---DatasphereClient wraps the Datasphere Catalog & Consumption APIs using httpx.

✅ Requirements

--Python: 3.10+ (tested with 3.14)
--A working SAP Datasphere tenant
--An OAuth client with:
-token URL,
-client ID,
-client secret,
-permission to call the Catalog & Consumption APIs.

This project is intended for technical users who are comfortable with:
-environment variables,
-basic command-line usage, and
-SAP Datasphere/SAP BTP concepts.

🚀 Installation (from GitHub source)

Until there is a PyPI release, the recommended install is from the repo.

1. Clone the repo
git clone https://github.com/rahulsethi/SAPDatasphereMCP.git
cd SAPDatasphereMCP

2. Create and activate a virtualenv

Windows (PowerShell):

python -m venv .venv
.\.venv\Scripts\Activate.ps1


macOS / Linux (bash/zsh):

python -m venv .venv
source .venv/bin/activate

3. Install the package in editable (dev) mode
pip install -e ".[dev]"


This installs:

the sap_datasphere_mcp package,

the sap-datasphere-mcp console script, and

dev tools like pytest for local tests.


⚙️ Configure SAP Datasphere credentials

The MCP server reads its configuration from environment variables
via DatasphereConfig.from_env().

At minimum you need:

DATASPHERE_TENANT_URL
Base URL of your Datasphere tenant,
e.g. https://your-tenant-id.eu10.hcs.cloud.sap

DATASPHERE_OAUTH_TOKEN_URL
OAuth token endpoint for your technical client,
e.g. https://your-uaa-domain/oauth/token

DATASPHERE_OAUTH_CLIENT_ID

DATASPHERE_OAUTH_CLIENT_SECRET

Optional:

DATASPHERE_VERIFY_TLS

"1" or unset: verify TLS certificates (default, recommended)

"0": disable TLS verification
(only if you’re behind a corporate proxy with self-signed certs)

Example: PowerShell helper script (Windows)

Create set-datasphere-env.ps1 in the project root:

$env:DATASPHERE_TENANT_URL        = "https://your-tenant-id.eu10.hcs.cloud.sap"
$env:DATASPHERE_OAUTH_TOKEN_URL   = "https://your-uaa-domain/oauth/token"
$env:DATASPHERE_OAUTH_CLIENT_ID   = "your-client-id"
$env:DATASPHERE_OAUTH_CLIENT_SECRET = "your-client-secret"

# Optional: skip TLS verification for self-signed corporate proxies
# (only if you understand the security implications)
$env:DATASPHERE_VERIFY_TLS = "0"

Write-Host "Datasphere environment variables set."


Then in each new shell:

.\set-datasphere-env.ps1


On macOS/Linux you can do the same with export in a shell script.


🧪 Local smoke tests

With env vars set and the virtualenv active:

pytest


Then try the demo scripts:

# List spaces via MCP tasks
python demo_mcp_list_spaces.py

# List assets in a specific space (set DATASPHERE_TEST_SPACE first)
python demo_mcp_list_assets.py

# Preview data
python demo_mcp_preview_filtered.py

# Describe schema
python demo_mcp_describe_asset.py

# Query with filter/sort/select/skip
python demo_mcp_query_relational.py

# Search assets by name
python demo_mcp_search_assets.py

# Summarise a space
python demo_mcp_space_summary.py

# Profile one column
python demo_mcp_profile_column.py


Each script prints the raw JSON-ish results so you can see
what MCP tools will return to an AI agent.


🖥️ Running the MCP server

To start the stdio server:

sap-datasphere-mcp


The process will listen on stdin/stdout using JSON-RPC as defined by MCP.

You normally don’t talk to this directly; an MCP-compatible client
(e.g. Claude Desktop) launches it and sends requests over stdio.


🤖 Using with Claude Desktop (example)

Exact config file locations differ by OS and Claude version;
see Anthropic’s documentation for up-to-date paths.

Conceptually, you add an entry under mcpServers
telling Claude how to start your server and what env vars to pass.

Example mcpServers entry (JSON with comments removed):

{
  "mcpServers": {
    "sap-datasphere": {
      "command": "sap-datasphere-mcp",
      "args": [],
      "env": {
        "DATASPHERE_TENANT_URL": "https://your-tenant-id.eu10.hcs.cloud.sap",
        "DATASPHERE_OAUTH_TOKEN_URL": "https://your-uaa-domain/oauth/token",
        "DATASPHERE_OAUTH_CLIENT_ID": "your-client-id",
        "DATASPHERE_OAUTH_CLIENT_SECRET": "your-client-secret",
        "DATASPHERE_VERIFY_TLS": "1"
      }
    }
  }
}

After editing the config, restart Claude Desktop.
The new MCP server should appear in the list of tools the model can call.

🔧 MCP tools

All tools live in sap_datasphere_mcp.tools.tasks
and are registered in the MCP server with the following names and signatures.

Health & discovery

datasphere_ping() → { "ok": bool }
Sanity check that config + OAuth at least look healthy.

datasphere_list_spaces() → { "spaces": [ {id, name, description}, ... ] }

datasphere_list_assets(space_id) →
{ "space_id": str, "assets": [ {id, name, type, space_id, description}, ... ] }

Data preview & schema

datasphere_preview_asset(space_id, asset_name, top=20, select=None, filter=None, order_by=None)
Returns:

{
  "columns": ["EMP_ID", "FIRST_NAME", ...],
  "rows": [[101, "Rudransh", ...], ...],
  "truncated": false,
  "meta": { "space_id": "...", "asset_name": "...", "row_count": 3, "top": 20 }
}

datasphere_describe_asset_schema(space_id, asset_name, top=20)
Uses a preview sample to infer basic column metadata:
example values, rough types, null counts (sample-based).

Relational querying

datasphere_query_relational(space_id, asset_name, select=None, filter=None, order_by=None, top=100, skip=0)
Same shape as datasphere_preview_asset, but exposes
$select, $filter, $orderby, $top, $skip.

This is still intentionally simple; complex analytical / OLAP use-cases
are out of scope for v0.1.

Search, summaries, profiling

datasphere_search_assets(query, space_id=None, limit=50)
Case-insensitive substring search on asset id / name
across one or all spaces.

datasphere_space_summary(space_id, max_assets=50)
Returns aggregate counts by asset type and a small sample list.

datasphere_profile_column(space_id, asset_name, column, top=100)
Builds a quick profile from sample rows:

inferred type list (e.g. ["int"]),

sample size,

null count,

distinct count,

for numeric columns: min, max, mean,

example values.

🗺️ Roadmap (future ideas)

These are not implemented yet, but are on the wish-list:

Analytical / cube-style query helpers for analytical models.

“Find assets by column name” across spaces.

Richer data profiling (histograms, categorical distributions, etc.).

Better error classification and human-friendly error messages.

Optional caching to reduce repeated calls to the same assets.

Additional transports (e.g. HTTP) if needed by other MCP clients.


📦 Versioning

0.1.0 – first public preview (current)

Basic connectivity, catalog, preview, schema, query, search & profiling tools.

Tested against a small sample dataset (EMP_View_Test)
in a single tenant/space.

Expect breaking changes in the 0.x series as the API evolves.


📄 License

This project is released under the MIT License.
See the LICENSE
 file for details.

You are free to use, modify, and redistribute the code, provided you keep
the copyright notice and license text in derivative works.

