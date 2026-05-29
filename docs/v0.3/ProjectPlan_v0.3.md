<!-- SAP Datasphere MCP Server -->
<!-- File: ProjectPlan_v0.3.md -->
<!-- Version: v2 -->

# Project Plan – SAP Datasphere MCP Server v0.3

This document describes scope, phases, and release criteria for **v0.3**.

v0.3 builds on v0.2 by adding:

- configurable **guardrails** (caps) and **TTL caching**
- a minimal **analytical query tool**
- deterministic **summary helpers**
- **plugin-ready** architecture (registry + env-based loading)

---

## Goals

### Product goals

- Keep the server **read-only** and safe for LLM usage.
- Make Datasphere exploration **faster** and **more deterministic** for agents:
  - predictable JSON shapes
  - explicit truncation and caps metadata
- Establish a stable foundation for future extensions via **plugins**.

### Engineering goals

- Improve resilience (token handling, errors, caps, caching).
- Expand test coverage for new v0.3 surfaces.
- Keep codebase small and maintainable.

---

## Non-goals

- Any write / admin / user-management actions.
- Complex OLAP semantics (derived measures, time-intelligence macros).
- “Translate vague prose into a perfect cube query” orchestration macros.
- Bulk export / ETL / replication features.

---

## Scope for v0.3 (in-scope)

### Core hardening & QoL

- Environment-driven caps for row-returning tools:
  - preview/query/profile/analytical/search
- Metadata-focused TTL cache:
  - reduce repeated calls for list/metadata/columns/summary tools
- Improve diagnostics output:
  - include cache stats and plugin status
- Keep mock mode functional for demos and tests.

### Basic analytical / OLAP access (minimal)

Introduce a single core analytical tool:

- `datasphere_query_analytical`
  - select/filter/order/top/skip pattern similar to relational query
  - uses analytical consumption endpoints under the hood (client layer)

Notes:
- v0.3 core does **not** add a dedicated `datasphere_list_analytical_models` tool.
  - discovery uses `datasphere_list_assets` + `datasphere_get_asset_metadata`
  - which already indicates whether an asset supports analytical queries.

Constraints:
- No complex calculations / derived measures / time-intelligence macros in v0.3.
- Tool stays in “minimal query surface” territory.

### Deterministic summaries (open-core)

Introduce small summary helpers that return **structured JSON** (deterministic, tool-friendly):

- `datasphere_summarize_asset`
  - builds on `datasphere_get_asset_metadata` + `datasphere_list_columns`
  - returns:
    - asset identity
    - keys (if known)
    - suggested measures/dimensions (heuristics)
    - API support + URLs

- `datasphere_summarize_space`
  - builds on `datasphere_space_summary`
  - returns:
    - total assets
    - top asset types
    - sample assets list

- `datasphere_summarize_column_profile`
  - wraps `datasphere_profile_column`
  - returns:
    - role hint (id/measure/dimension)
    - null fraction
    - numeric/categorical highlights

### Comparison helper (open-core)

- `datasphere_compare_assets_basic`
  - compares two assets by column names:
    - common columns, differences
    - simple similarity score
    - join-key hints (keys/id-like columns)

### Plugin-ready architecture

Introduce a minimal plugin system:

- `sap_datasphere_mcp.plugins.registry`:
  - reads env `DATASPHERE_PLUGINS`
  - imports plugin modules
  - each plugin module exposes `register_tools(server)`

Transport startup should:
1. register **core** tools (`tools/tasks.py`)
2. load optional plugin tools via registry

Requirements:
- Plugin import/registration failures are warnings, not fatal.
- Plugin status should be observable via:
  - `datasphere_plugins_status`
  - included in `datasphere_diagnostics`

---

## Phases & milestones

### Phase A – Planning & Documentation
- Finalize v0.3 scope and naming.
- Update:
  - `ProjectPlan_v0.3.md`
  - `ImplementationTracker_v0.3.md`
  - `Architecture.md`
  - `TestPrompts_v0.3.md`
  - `CHANGELOG.md`

Exit criteria:
- All docs reflect actual tool names and behaviors.

### Phase B – Core Hardening & QoL
- Caps & meta fields (requested vs effective).
- TTL cache.
- OAuth hardening (token caching, clearer errors).
- Tests for caps/caching behavior.

Exit criteria:
- Unit tests cover new hardening paths.
- Mock mode remains green.

### Phase C – Analytical + Summaries
- Implement `datasphere_query_analytical`.
- Implement deterministic summary tools.
- Add/update tests and test prompts.

Exit criteria:
- New tools have stable JSON contracts and are documented.

### Phase D – Plugin system
- Implement registry + env loading.
- Add plugin observability tool and diagnostics integration.

Exit criteria:
- Core starts even if plugins fail.
- `datasphere_plugins_status` and diagnostics show plugin state.

### Phase E – Release: packaging & public docs
- Update public `README.md` (feature overview, tool list, config).
- Bump version to `0.3.0` in `pyproject.toml`.
- Run:
  - `python -m compileall src/sap_datasphere_mcp`
  - `pytest`
- Tag and publish to GitHub + PyPI.

---

## Release criteria (v0.3)

v0.3 is ready when:

1. **Safety & scope**
   - Still read-only (no write/admin tools).
   - Caps enforced and visible via meta fields.

2. **Core features**
   - `datasphere_query_analytical` works (or fails clearly) in real and mock contexts.
   - Summary helpers return deterministic, stable shapes.
   - Cache reduces repeated metadata calls.

3. **Quality**
   - Tests are green and cover new surfaces.
   - Test prompts updated for new tools.

4. **Docs & packaging**
   - `Architecture.md`, `ProjectPlan_v0.3.md`, `TestPrompts_v0.3.md`, `CHANGELOG.md` aligned.
   - `README.md` updated last (public-facing).
   - Package version bumped and release steps verified.

---

## Notes & decisions

- Tool names finalized:
  - `datasphere_query_analytical` (no `_basic`)
  - `datasphere_summarize_*` (American spelling for tool names)
- No `datasphere_list_analytical_models` in core v0.3; discovery uses metadata.
- Plugin failures must not block core startup; plugin status is observable.
