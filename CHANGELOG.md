<!-- SAP Datasphere MCP Server -->
<!-- File: CHANGELOG.md -->
<!-- Version: v5 -->

# Changelog

All notable changes to this project are documented here. This file at the
repository root is the canonical changelog.

---

## 1.0.0 – Family-aligned graduation release

> Released 2026-07-13. The first 1.x release of `SAPDatasphereMCP`.
> Renames, governance, and the MCP whitespace plays Mario hadn't taken — bundled into one coherent breaking change so users absorb the cost once.

### Added

- **24 MCP tools** in 7 categories (`connectivity`, `catalog`, `query`, `discover`, `profile`, `summarize`, `governance`). 22 ported from v0.3.x; 2 new governance tools: `datasphere_governance_api_policy_check` and `datasphere_governance_audit_tail`.
- **MCP Prompts (5)** — `profile_dataset`, `audit_space`, `explain_analytical_model`, `compare_assets`, `find_data_about_topic`. First SAP MCP server to ship prompts.
- **MCP Resources (4)** — URI-addressable catalog content under `datasphere://space/{id}` and three nested forms. First SAP MCP server to ship resources.
- **MCP tool annotations** (`readOnlyHint`/`idempotentHint`/`destructiveHint`) on every tool. Every tool is `readOnly`; none are `destructive`.
- **Governance layer ported from sibling SAPBDCMCP**: `audit.py` (JSONL audit log), `policy.py` + `policy_evidence.py` (SAP API Policy v4/2026 gate + disclosure), `redaction.py` (secret/PII scrubbing), `tools/_metadata.py` (per-tool risk metadata), `tools/_gated.py` (interceptor chain).
- **mTLS-bound OAuth client_credentials (Tier C) documented as a deployment posture** — `DATASPHERE_OAUTH_MTLS_CERT` / `DATASPHERE_OAUTH_MTLS_KEY` are recognized and reported by `datasphere_governance_api_policy_check`. Binding them into the OAuth token flow itself is on the roadmap and **not yet implemented** in `auth.py` (see the Deferred section).
- **HTTP transport bearer auth** — set `DATASPHERE_MCP_BEARER_TOKEN`.
- **`server.create_server()` factory** shared by both transports; `python -m sap_datasphere_mcp` works.
- **npx distribution** — `npx-wrapper/` ships `@rahulsethi/sap-datasphere-mcp`, a Node bootstrap that probes uvx → pipx → python3 and forwards stdio.
- **CI workflow** — `.github/workflows/ci.yml` runs pytest on Linux/macOS/Windows × Python 3.11/3.12/3.13, plus ruff and a build step.
- **`CONTRIBUTING.md`, `MANIFEST.in`, `.editorconfig`, `.env.example`** ported from sibling.
- **`public_docs/`** — user-facing docs: `README`, `INSTALLATION`, `QUICKSTART`, `TOOLS`, `MIGRATION`, `SAP_API_POLICY`, `COMMERCIAL_LICENSING`.
- **`docs/v1.0/`** — full design set: `ProjectPlan_v1.0.md`, `Architecture_v1.0.md`, `Decisions_v1.0.md` (12 ADRs), `ImplementationTracker_v1.0.md`.
- **13 new pytest tests** covering registry, governance, prompts/resources wiring, redaction, policy gate, alias deprecation. Total suite: 34 tests, all green.

### Changed

- **All 22 v0.3.x tool names** renamed to `datasphere_<category>_<verb>`. Old names remain registered as deprecation aliases through v1.1; aliases emit a one-time-per-process structured-log warning. See `public_docs/MIGRATION.md` for the full mapping table.
- **PyPI distribution name retained** as `mcp-sap-datasphere-server`. (A planned rename to `sap-datasphere-mcp` was reverted — that short name is taken by an unrelated community package.) The console script `sap-datasphere-mcp` and Python import path `sap_datasphere_mcp` are unchanged; a `mcp-sap-datasphere-server` console-script alias was added so `uvx mcp-sap-datasphere-server` resolves the server.
- **Default API path order** flipped: clients try `/api/v1/datasphere/...` first, falling back to `/api/v1/dwc/...` only on 404/405. Set `DATASPHERE_API_PATH_LEGACY=1` to revert.
- **Python floor bumped** 3.10 → 3.11.
- **`mcp` SDK pin bumped** `>=1.2.0` → `mcp[cli]>=1.25.0`. Added `python-dotenv>=1.0.1` and `jsonschema>=4.20.0` as deps.
- **`tools/` reorganized** into per-category facade modules + a single `registry.py`. Async implementations remain in `tools/tasks.py` (ADR-011 defers deeper code split to a future release).
- **README rewrite** with family section pointing at SAPBDCMCP, MCP Gateway recommendation, and a per-tool risk table.
- **CHANGELOG taxonomy expanded** to mirror sibling: Added / Changed / Deprecated / Removed / Fixed / Licensing / Deferred / Migration.

### Deprecated

- All 22 v0.3.x tool names (e.g. `datasphere_ping`, `datasphere_list_spaces`). Removed in v1.2.
- Legacy `/api/v1/dwc/*` API path tree. Supported by SAP through March 2027.
- `tasks.register_tools(server)` direct call — superseded by `tools.registry.register_all(server)` (called by `server.create_server()` automatically).

### Removed

- Python 3.10 support.

### Fixed

- Audit failures no longer break tool calls — the audit writer swallows `OSError` so disk problems don't propagate.
- Redaction is conservative by default — patterns restricted to fields whose key names look like secrets, plus universal JWT/Bearer scrubbing. Avoids false positives in legitimate enterprise data.

### Licensing

- **Relicensed from MIT to the Business Source License 1.1 (BSL 1.1)** (v1.0+), which converts automatically to Apache 2.0 on 2029-01-01. Versions v0.3.1 and earlier remain MIT-licensed and are unaffected. Personal, research, academic, and internal evaluation use is free under the Additional Use Grant; commercial use requires a separate commercial license — see [`COMMERCIAL_LICENSING.md`](COMMERCIAL_LICENSING.md) for the friendly path. Same license arrangement as sibling [SAPBDCMCP](https://github.com/rahulsethi/SAPBDCMCP); 2-for-1 family discount available on request.

### Deferred (will land in 1.0.x / 1.1)

- Per-tool `outputSchema` JSON Schemas under `src/.../schemas/`.
- Opaque cursor-based pagination for list/discover tools.
- `npx:`/`uvx:`/`cmd:` subprocess plugin upstreams in `plugins/registry.py`.
- Data Product tools (the SAP-endorsed BDC agent surface).
- SAP Knowledge Graph integration; lineage / data quality first-class tools.
- Anthropic MCP registry application.

### Migration

If you're upgrading from v0.3.x, see [`public_docs/MIGRATION.md`](public_docs/MIGRATION.md). Short version:

```bash
pip install --upgrade mcp-sap-datasphere-server
# or: uvx mcp-sap-datasphere-server
# or: npx -y @rahulsethi/sap-datasphere-mcp
```

The PyPI distribution name is unchanged (`mcp-sap-datasphere-server`) — just upgrade in place. Old tool names continue to work through v1.1 with deprecation logs. Update your Claude Desktop / Cursor configs before v1.2.

---

## 0.3.1 – Cleanup & reorganization

> Patch release. No behavior changes, no public API changes.

### Changed

- **Repository layout** — `demo_*.py` and ad-hoc `test_*.py` scripts moved from
  the repo root into a new `examples/` directory. The four `smoke_*.py` scripts
  are renamed (from `test_*.py`) so pytest no longer collects them. The
  automated test suite remains in `tests/`.
- **`docs/` is now tracked** — the previous `.gitignore` accidentally excluded
  the whole documentation folder. Architecture notes, the backlog, version
  plans, and the historical changelog mirror are now part of the repo.
- **`set-datasphere-env.example.ps1`** added as a sanitized template. The local
  `set-datasphere-env.ps1` continues to be gitignored.

### Removed

- **Dead `tools/` submodules** — `tools/catalog.py`, `tools/spaces.py`,
  `tools/connections.py`, `tools/data.py`, and the unused
  `tools/__init__.py:register_all_tools()` helper. The active boot path goes
  directly through `tools/tasks.register_tools()`; nothing imported the deleted
  modules.
- **`src/sap_datasphere_mcp/test_list_assets.py`** — stray smoke script that
  lived inside the installable package. Moved to `examples/smoke_list_assets.py`.
- **`demo_claude_desktop/SAPDatasphere_MCP_rahulsethi.mp4`** (18 MB) — removed
  from the working tree to reduce clone size for new contributors. The blob
  remains in git history; the video itself can be linked from a GitHub Release.
- **Stale `dist/` 0.3.0 build artifacts** and root `__pycache__/`.

### Fixed

- **`.gitignore`** — removed the line that excluded `docs/` from the repo,
  added `.claude/settings.local.json`, added a case-insensitive `[Nn]ew folder/`
  pattern, and added `.ruff_cache/` alongside the existing `ruff_cache/`.

---

## 0.3.0 – Analytical querying, summaries & guardrails

### Added

- Configurable guardrails for row-returning tools and search results (caps enforced in tool layer).
- Metadata-focused TTL cache to reduce repeated backend calls for discovery/metadata tools.
- Analytical querying tool: `datasphere_query_analytical`.
- Deterministic summary tools:
  - `datasphere_summarize_asset`
  - `datasphere_summarize_space`
  - `datasphere_summarize_column_profile`
- Asset comparison helper: `datasphere_compare_assets_basic`.
- Plugin observability tool: `datasphere_plugins_status` (also surfaced in diagnostics output).

### Changed

- Tool responses now include clearer `meta` fields (requested vs effective limits, cap applied flags) to make truncation explicit.
- OAuth client hardened (client-credentials via HTTP Basic auth + token caching + clearer errors).
- Config expanded for TLS verification toggle, caps, and cache settings.

### Fixed

- Normalized handling for optional query metadata to avoid `None`-shaped surprises in tool responses.

---

## 0.2.0 – Metadata & Diagnostics expansion

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
