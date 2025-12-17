<!-- SAP Datasphere MCP Server -->
<!-- File: CHANGELOG.md -->
<!-- Version: v2 -->

# Changelog

All notable changes to this project are documented here.

---

## 0.2.0 – Metadata & Diagnostics expansion

> Status: in development / preview.

### Added

- **Catalog metadata helper**
  - `datasphere_get_asset_metadata` to fetch labels, descriptions, type and
    relational/analytical exposure flags for a single asset, plus raw payload.

- **Column-level introspection**
  - `datasphere_list_columns` to list columns using relational `$metadata`
    (EDMX/XML) when available, with preview-based fallback.

- **Column search across spaces**
  - `datasphere_find_assets_with_column` to find assets exposing a given column
    in a single space.
  - `datasphere_find_assets_by_column` to search across multiple spaces with
    limits on spaces and assets scanned.

- **Richer column profiling**
  - Extended `datasphere_profile_column` with:
    - numeric percentiles (p25, p50, p75),
    - IQR and Tukey-style fences,
    - outlier count,
    - categorical summary for low-cardinality columns,
    - heuristic `role_hint` (`"id"`, `"measure"`, `"dimension"`).

- **Diagnostics & identity helpers**
  - `datasphere_diagnostics` to run high-level MCP & tenant health checks.
  - `datasphere_get_tenant_info` to inspect redacted configuration (URLs, region hint, TLS, OAuth presence).
  - `datasphere_get_current_user` to describe the current identity context
    (technical user vs mock mode) without exposing secrets.

- **Mock mode**
  - Support for `DATASPHERE_MOCK_MODE=1`, enabling a small in-memory demo
    dataset for local testing and demos without a real tenant.

- **Packaging metadata**
  - `pyproject.toml` updated with:
    - project name `mcp-sap-datasphere-server` (planned PyPI distribution name),
    - explicit `src/sap_datasphere_mcp` package configuration for Hatch.

### Changed

- `datasphere_profile_column` now returns a richer `numeric_summary` and
  optional `categorical_summary` and `role_hint`.
- Internals of `tools/tasks.py` refactored to support both real `DatasphereClient`
  and `MockDatasphereClient`.
- Documentation updated to:
  - distinguish clearly between v0.1.0 and v0.2.0 features,
  - describe diagnostics, mock mode and metadata tools,
  - mention the planned PyPI distribution name.

### Fixed

- Improved error handling and more structured `meta` blocks in several tools.
- Clarified documentation around environment variables and TLS verification.

---

## 0.1.0 – First public preview

> Initial GitHub release.

### Added

- **Health & connectivity**
  - `datasphere_ping` to check basic configuration & OAuth.

- **Spaces & catalog**
  - `datasphere_list_spaces` to list visible Datasphere spaces.
  - `datasphere_list_assets` to list catalog assets in a given space.

- **Data preview & relational querying**
  - `datasphere_preview_asset` for small row samples.
  - `datasphere_query_relational` for simple `$select` / `$filter` /
    `$orderby` / `$top` / `$skip` queries.

- **Schema & profiling**
  - `datasphere_describe_asset_schema` for sample-based column summaries.
  - `datasphere_profile_column` for basic column profiling
    (counts, distincts, min / max / mean for numeric columns).

- **Search & summaries**
  - `datasphere_search_assets` for fuzzy search across spaces.
  - `datasphere_space_summary` for quick space-level overviews.

- **Tooling & demos**
  - Initial demo scripts (`demo_mcp_*`) for local smoke tests.
  - Basic documentation and instructions for using the MCP server with
    Claude Desktop.
