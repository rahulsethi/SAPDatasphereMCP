<!-- SAP Datasphere MCP Server -->
<!-- File: README.md -->
<!-- Version: v1-public -->

# SAP Datasphere MCP Server

An MCP (Model Context Protocol) server that exposes **SAP Datasphere** as a set of tools and resources for AI agents.

- **Goal:** Provide safe, read-only access to SAP Datasphere spaces, assets, metadata, and data via a standard MCP interface.
- **Usage:** Can be plugged into any MCP-compatible agent or custom automation that speaks MCP.

---

## Features

### Implemented MCP tools

| MCP tool                         | What it does                                                                                     |
| -------------------------------- | ------------------------------------------------------------------------------------------------- |
| `datasphere_ping`                | Lightweight health check that verifies configuration is sane.                                    |
| `datasphere_list_spaces`         | Lists Datasphere spaces visible to the OAuth client.                                             |
| `datasphere_list_assets`         | Lists catalog assets (tables/views/models) in a given space.                                     |
| `datasphere_preview_asset`       | Fetches a small sample of rows from a relational asset. Supports `$top`, `$select`, `$filter`, `$orderby`. |
| `datasphere_describe_asset_schema` | Samples data and infers per-column info (example values, null counts, friendly types).          |
| `datasphere_query_relational`    | Runs a parameterised relational query with `$select`, `$filter`, `$orderby`, `$top`, `$skip`.    |

These are enough for an agent to:

- Discover spaces and assets.
- Inspect the shape of a single asset.
- Run small, targeted queries over relational datasets.

### Roadmap (short version)

Planned additions include:

- Asset search by name/description.
- Asset metadata and explicit column lists.
- Space summaries (asset counts, sample assets, timestamps).
- Column-based discovery (“find assets with column X”).
- Optional richer profiling (distinct counts, min/max, etc.).

More advanced ideas (analytical models, lineage, mock mode) are tracked in `docs/ProjectPlan.md`.

---

## Getting Started

### Requirements

- Python **3.11+**
- Access to an SAP Datasphere tenant
- A technical OAuth client in the same BTP subaccount, using client-credentials flow

### Install

```bash
git clone https://github.com/rahulsethi/SAPDatasphereMCP.git
cd SAPDatasphereMCP

python -m venv .venv
.\.venv\Scripts\Activate.ps1   # or source .venv/bin/activate on macOS/Linux

pip install -e ".[dev]"

###Configure environment

$env:DATASPHERE_TENANT_URL      = "https://<your-tenant>.hcs.cloud.sap"
$env:DATASPHERE_OAUTH_TOKEN_URL = "https://<your-auth-subdomain>.authentication.<region>.hana.ondemand.com/oauth/token"
$env:DATASPHERE_CLIENT_ID       = "<your-client-id>"
$env:DATASPHERE_CLIENT_SECRET   = "<your-client-secret>"

You can store these in a helper script (e.g. set-datasphere-env.ps1) and source it before use.

###Sanity checks

-- With env vars set and the virtualenv active:

pytest

python demo_mcp_list_spaces.py
python demo_mcp_list_assets.py
python demo_mcp_preview_filtered.py
python demo_mcp_describe_asset.py
python demo_mcp_query_relational.py


###Running the MCP server

sap-datasphere-mcp


The process will listen on stdin/stdout using JSON-RPC as defined by MCP.

Any MCP-compatible host can connect and use the tools listed above.