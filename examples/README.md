# Examples & smoke scripts

This folder contains runnable scripts that exercise the SAP Datasphere MCP
server end-to-end against a real tenant (or in mock mode). They are **not**
part of the automated pytest suite (which lives in `tests/`) — they are here so
you can dogfood the tools interactively and confirm your environment is wired
correctly.

## Prerequisites

1. Install the package in editable mode (from the repo root):

   ```bash
   pip install -e ".[dev]"
   ```

2. Set your Datasphere credentials. On Windows / PowerShell:

   ```powershell
   # Copy the template and fill in real values, then dot-source it
   Copy-Item ..\set-datasphere-env.example.ps1 ..\set-datasphere-env.ps1
   # ... edit the file ...
   . ..\set-datasphere-env.ps1
   ```

   Or run in mock mode with no real tenant:

   ```powershell
   $env:DATASPHERE_MOCK_MODE = "1"
   ```

3. Some scripts honor `DATASPHERE_TEST_SPACE` to pick a specific space.

## Demo scripts (`demo_*.py`)

End-to-end demonstrations of individual MCP tools. Each script invokes one
tool, prints the JSON-like result, and exits.

| Script | What it shows |
|---|---|
| `demo_list_assets.py` | `DatasphereClient.list_space_assets()` — bypasses the MCP tool layer |
| `demo_mcp_list_spaces.py` | `datasphere_list_spaces` MCP tool |
| `demo_mcp_list_assets.py` | `datasphere_list_assets` MCP tool |
| `demo_mcp_describe_asset.py` | `datasphere_describe_asset_schema` MCP tool |
| `demo_mcp_preview_filtered.py` | `datasphere_preview_asset` with an OData filter |
| `demo_mcp_profile_column.py` | `datasphere_profile_column` MCP tool |
| `demo_mcp_query_relational.py` | `datasphere_query_relational` with select / filter / orderby / paging |
| `demo_mcp_search_assets.py` | `datasphere_search_assets` MCP tool |
| `demo_mcp_space_summary.py` | `datasphere_space_summary` MCP tool |

Run any of them with the package on your `PYTHONPATH`:

```bash
python examples/demo_mcp_list_spaces.py
```

## Smoke tests (`smoke_*.py`)

Lightweight sanity scripts used during development to verify the underlying
HTTP/OData wiring against a live tenant. They hit real Datasphere endpoints
and print results to stdout.

| Script | What it checks |
|---|---|
| `smoke_list_assets.py` | Catalog `list_space_assets` via `DatasphereClient` |
| `smoke_list_spaces.py` | Catalog `/api/v1/dwc/catalog/spaces` via raw `httpx` |
| `smoke_mcp_preview_tool.py` | `preview_asset` MCP tool wiring (`tools.tasks` → `DatasphereClient`) |
| `smoke_preview_asset.py` | `DatasphereClient.preview_asset_data()` directly |

These are intentionally renamed from `test_*` to `smoke_*` so pytest never
picks them up — they are not assertion-based tests.
