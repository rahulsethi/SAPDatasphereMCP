<!-- SAP Datasphere MCP Server -->

<!-- File: ProjectPlan\_v0.2.md -->

<!-- Version: v1 -->



\# Project Plan – SAP Datasphere MCP Server v0.2



This document describes the scope, phases, and release criteria for \*\*v0.2\*\* of the SAP Datasphere MCP Server.



It builds on v0.1 (read-only core tools for spaces, assets, preview, schema, relational query, search, and profiling) and adds richer metadata, better profiling, diagnostics, and PyPI packaging.



---



\## 1. Context



\### 1.1 v0.1 recap



v0.1 delivered a \*\*read-only MCP server\*\* for SAP Datasphere:



\- `DatasphereConfig` + `OAuthClient` + `DatasphereClient` to wrap tenant config, OAuth, and REST calls.

\- Core MCP tools for:

&nbsp; - listing spaces and assets,

&nbsp; - previewing relational assets,

&nbsp; - describing schema (sample-based),

&nbsp; - running simple relational queries,

&nbsp; - basic search/summaries and column profiling.

\- Stdio-based MCP server using FastMCP, validated via \*\*Claude Code\*\* sanity tests.



This version established the basic architecture and proved that Datasphere can be safely exposed to LLMs via MCP.



\### 1.2 Motivation for v0.2



Between v0.1 and now:



\- We identified left-over items from the original plan (metadata tools, richer profiling, diagnostics, mock mode, more tests).

\- A parallel open-source project appeared with a very broad (44-tool) Datasphere MCP server, focused on \*\*admin + ETL + production deployment\*\*.

\- Our goal is deliberately different:

&nbsp; - stay \*\*strictly read-only\*\*,

&nbsp; - be \*\*AI-first and LLM-friendly\*\*,

&nbsp; - keep the codebase \*\*small, clear, and SDK-like\*\*, with MCP as a thin layer.



v0.2 is about strengthening the \*\*core connector\*\*: better metadata, smarter profiling, observable behaviour, and easy installation (PyPI), without expanding into risky admin functionality.



---



\## 2. Scope for v0.2



\### 2.1 In-scope (v0.2)



\*\*A. Metadata \& discovery\*\*



\- Asset-level metadata tooling:

&nbsp; - `datasphere\_get\_asset\_metadata` – richer information from catalog/metadata APIs.

&nbsp; - `datasphere\_list\_columns` – explicit list of columns and types for a given asset.

\- Column-based discovery:

&nbsp; - `datasphere\_find\_assets\_by\_column` – cross-space search for “assets that contain column X”.

\- Underlying `DatasphereClient` enhancements to call metadata endpoints directly instead of only inferring from samples.



\*\*B. Column profiling \& AI semantics\*\*



\- Richer numeric distributions:

&nbsp; - percentiles, interquartile-range (IQR) outlier hints, min/max, etc.

\- Basic categorical profiling:

&nbsp; - most frequent values and their frequencies for low-cardinality columns.

\- Optional semantic hints:

&nbsp; - “likely role” classification (ID / measure / dimension) based on names and stats.

\- Either extension of `datasphere\_profile\_column` or a new `datasphere\_analyze\_column`-style tool (API to be finalised).



\*\*C. Diagnostics, error model, logging \& caching\*\*



\- Structured error taxonomy for all tools (e.g. `AUTH\_ERROR`, `NETWORK\_ERROR`, `API\_LIMITATION`, `VALIDATION\_ERROR`).

\- `datasphere\_diagnostics` tool:

&nbsp; - checks auth + connectivity to catalog and consumption endpoints,

&nbsp; - returns a simple health report.

\- Optional read-only identity helpers:

&nbsp; - `datasphere\_get\_tenant\_info`, `datasphere\_get\_current\_user` (minimal, no secrets).

\- End-to-end `DATASPHERE\_MOCK\_MODE`:

&nbsp; - ability to run the server with mock data for local development and tests.

\- Lightweight in-memory caching for:

&nbsp; - `list\_spaces`,

&nbsp; - `list\_space\_assets`,

&nbsp; - metadata calls.

\- Improved logging:

&nbsp; - consistent log format,

&nbsp; - correlation IDs when Datasphere returns them.



\*\*D. Packaging, docs \& release\*\*



\- PyPI packaging under a unique name (tentative: `sap-datasphere-mcp-server`).

\- CLI entrypoint matching the package (e.g. `sap-datasphere-mcp-server`).

\- Updated `pyproject.toml` with version `0.2.0` and accurate metadata.

\- Documentation updates:

&nbsp; - public `README.md` for v0.2,

&nbsp; - internal docs (v0.2 plan, tracker, etc.),

&nbsp; - short “tool catalog” overview.

\- Final sanity test with at least one MCP client (Claude Code) using the PyPI-installed server.



---



\### 2.2 Out-of-scope for v0.2



The following are \*\*explicitly not part of v0.2\*\* and live in `backlog.md`:



\- DevAssist/Sethi integration:

&nbsp; - no orchestration, agents, or cross-system flows in this release.

\- Destructive/admin features:

&nbsp; - database user creation/update/delete/reset,

&nbsp; - grants/roles management,

&nbsp; - direct ETL/export tools for large volumes.

\- New transports:

&nbsp; - HTTP server mode or long-lived service deployment.

\- Advanced analytics helpers:

&nbsp; - full OLAP/analytical navigation,

&nbsp; - automatic join-path discovery,

&nbsp; - time-series specific analysis.



These may appear in later versions (v0.3+), but v0.2 focuses on the core connector and packaging.



---



\## 3. Architecture Impact



\### 3.1 Existing architecture (v0.1 baseline)



High-level layers (unchanged conceptually):



\- \*\*Config \& OAuth\*\*

&nbsp; - `DatasphereConfig` – tenant URL, OAuth token URL, client ID/secret, TLS/mocking options.

&nbsp; - `OAuthClient` – client-credentials grant, token caching.

\- \*\*Datasphere client\*\*

&nbsp; - `DatasphereClient` – wraps catalog and relational APIs.

\- \*\*MCP server\*\*

&nbsp; - FastMCP-based stdio server, registering `datasphere\_\*` tools that call `DatasphereClient`.



\### 3.2 Changes in v0.2



\- \*\*DatasphereClient extension\*\*

&nbsp; - New methods for metadata endpoints (asset metadata, column lists, cross-space queries).

&nbsp; - Optional analytical support (if P2 analytical query work lands in this release).

\- \*\*Error model\*\*

&nbsp; - New structured error class/shape used consistently by all client methods.

\- \*\*Caching\*\*

&nbsp; - Internal in-memory cache object (simple TTL map) used inside `DatasphereClient` for read-heavy endpoints.

\- \*\*Diagnostics\*\*

&nbsp; - New diagnostics helper(s) that orchestrate multiple client calls and summarise the result.

\- \*\*No change in trust model\*\*

&nbsp; - Still \*\*read-only\*\*; no write/admin methods are added to the client.

&nbsp; - Still stdio-based MCP; no new transport layer in v0.2.



---



\## 4. Phases \& Milestones



The phases here mirror `ImplementationTracker\_v0.2.md`, but at a higher level.



\### Phase A – Planning \& Documentation



\*\*Objective:\*\* Lock v0.2 scope, positioning, and docs.



Key activities:



\- Finalise v0.2 goals, in-scope and out-of-scope areas.

\- Create and maintain:

&nbsp; - `ProjectPlan\_v0.2.md` (this file),

&nbsp; - `ImplementationTracker\_v0.2.md`,

&nbsp; - `backlog.md` for future work.

\- Decide:

&nbsp; - PyPI package + CLI names,

&nbsp; - whether to stay MIT for v0.2 (default) or change license going forward.



\*\*Exit criteria:\*\*



\- v0.2 scope is written down and stable.

\- Backlog clearly lists DevAssist integration and other future features.

\- Naming decisions for PyPI/CLI captured in Notes \& Decisions.



---



\### Phase B – Metadata \& Discovery



\*\*Objective:\*\* Provide stronger discovery and metadata capabilities.



Key activities:



\- Design JSON contract for new tools:

&nbsp; - `datasphere\_get\_asset\_metadata`,

&nbsp; - `datasphere\_list\_columns`,

&nbsp; - `datasphere\_find\_assets\_by\_column`.

\- Implement supporting `DatasphereClient` methods for metadata endpoints.

\- Implement and test the MCP tools.

\- Update docs with clear examples for these tools.



\*\*Exit criteria:\*\*



\- New tools are implemented and covered by unit tests.

\- Basic integration tests run against a real tenant (or mock mode) for at least one space.

\- README lists and describes the new metadata tools.



---



\### Phase C – Column Profiling \& Data Access Enhancements



\*\*Objective:\*\* Make column introspection more useful to LLMs, without expanding the data-access surface too much.



Key activities:



\- Decide whether to extend `datasphere\_profile\_column` or introduce a new tool.

\- Implement richer numeric stats and categorical profiling.

\- Add semantic hints (likely role) based on names + stats.

\- Add more tests around:

&nbsp; - query shapes,

&nbsp; - paging and limits,

&nbsp; - error behaviour for invalid filters/orders.

\- Refresh demo scripts for MCP usage (preview, describe, query, profiling).



\*\*Exit criteria:\*\*



\- Profiling tools return a stable, documented JSON shape.

\- Tests confirm behaviour on numeric, categorical, and edge-case columns.

\- Demo scripts run successfully against a known relational asset.



---



\### Phase D – Diagnostics, Error Model, Logging \& Caching



\*\*Objective:\*\* Make the server easier to observe, debug, and operate.



Key activities:



\- Introduce a structured error taxonomy and ensure all client methods use it.

\- Implement `datasphere\_diagnostics`:

&nbsp; - checks auth,

&nbsp; - lists spaces,

&nbsp; - performs a basic preview/query,

&nbsp; - returns a summarised health report.

\- Implement read-only identity helpers (tenant/user) if they prove useful and safe.

\- Wire `DATASPHERE\_MOCK\_MODE` end-to-end:

&nbsp; - deterministic mock responses for key tools.

\- Add lightweight caching for high-frequency read endpoints.

\- Improve logging with correlation IDs (when available) and consistent formatting.



\*\*Exit criteria:\*\*



\- Diagnostic tool returns a meaningful “OK / degraded / failed” style response.

\- Errors from all tools have consistent shape and include the error type.

\- Mock mode is usable for local development (no real Datasphere calls).

\- Basic logging helps trace requests without drowning the logs.



---



\### Phase E – Packaging, Docs \& Release



\*\*Objective:\*\* Ship v0.2 as a PyPI package and document it properly.



Key activities:



\- Finalise package name + CLI and update `pyproject.toml`.

\- Create build and publish workflow for PyPI (manual or CI).

\- Update `README.md`:

&nbsp; - short introduction and positioning,

&nbsp; - installation instructions (PyPI),

&nbsp; - configuration (env vars),

&nbsp; - basic usage with an MCP client,

&nbsp; - summary of tool categories.

\- Ensure `README\_internal.md` and architecture docs reflect v0.2 design.

\- Run end-to-end sanity test using a PyPI-installed version with Claude Code.



\*\*Exit criteria:\*\*



\- Package `sap-datasphere-mcp-server` (or final chosen name) is live on PyPI.

\- Version tagged in Git (e.g. `v0.2.0`) with a short changelog.

\- Sanity test verified with at least one MCP client (Claude Code) using PyPI install.

\- Docs describe v0.2 accurately and clearly.



---



\## 5. Tool Surface Snapshot (v0.2)



This is a rough view of where the tool set is heading by the end of v0.2.



\### 5.1 Existing core tools (from v0.1)



\- Health \& discovery:

&nbsp; - `datasphere\_ping`

&nbsp; - `datasphere\_list\_spaces`

&nbsp; - `datasphere\_list\_assets`

\- Data \& schema:

&nbsp; - `datasphere\_preview\_asset`

&nbsp; - `datasphere\_describe\_asset\_schema`

&nbsp; - `datasphere\_query\_relational`

\- Search \& profiling:

&nbsp; - `datasphere\_search\_assets`

&nbsp; - `datasphere\_space\_summary`

&nbsp; - `datasphere\_find\_assets\_with\_column` (per-space)

&nbsp; - `datasphere\_profile\_column`



\### 5.2 New/extended tools in v0.2 (planned)



\- Metadata \& discovery:

&nbsp; - `datasphere\_get\_asset\_metadata`

&nbsp; - `datasphere\_list\_columns`

&nbsp; - `datasphere\_find\_assets\_by\_column` (cross-space)

\- Profiling:

&nbsp; - extended `datasphere\_profile\_column` or new `datasphere\_analyze\_column` with richer stats.

\- Diagnostics \& identity:

&nbsp; - `datasphere\_diagnostics`

&nbsp; - possibly `datasphere\_get\_tenant\_info`

&nbsp; - possibly `datasphere\_get\_current\_user`



Exact naming may be refined during implementation, but the categories and responsibilities will stay consistent.



---



\## 6. Release Criteria – v0.2



v0.2 is considered \*\*ready to release\*\* when:



1\. \*\*Core functionality\*\*

&nbsp;  - Metadata tools and profiling enhancements are implemented and tested.

&nbsp;  - Diagnostics tool and error taxonomy are in place.

&nbsp;  - Caching and mock mode work for their intended scenarios.



2\. \*\*Safety \& scope\*\*

&nbsp;  - No tool performs write/admin actions; the server remains read-only.

&nbsp;  - Row limits and other safeguards are documented and enforced where needed.



3\. \*\*Quality\*\*

&nbsp;  - Unit tests cover main client methods and tool logic.

&nbsp;  - At least one end-to-end test has been run against a real Datasphere tenant.

&nbsp;  - Mock mode is usable for development without network calls.



4\. \*\*Packaging \& docs\*\*

&nbsp;  - PyPI package is published and installable.

&nbsp;  - README(s) and architecture docs describe v0.2 accurately.

&nbsp;  - A short changelog entry summarises the differences from v0.1.



---



\## 7. Risks \& Mitigations



\- \*\*Metadata API limitations / quirks\*\*

&nbsp; - \*Risk\*: Some catalog/metadata endpoints may behave inconsistently or return large payloads.

&nbsp; - \*Mitigation\*: Start with a narrow metadata subset; introduce pagination/limits; document any known API workarounds.



\- \*\*Profiling performance\*\*

&nbsp; - \*Risk\*: Poorly designed profiling queries could scan too much data.

&nbsp; - \*Mitigation\*: Use sampling; enforce limits; make profiling opt-in and clearly documented.



\- \*\*PyPI packaging friction\*\*

&nbsp; - \*Risk\*: Build or dependency issues delay release.

&nbsp; - \*Mitigation\*: Test build locally early; keep dependencies minimal; add a small smoke-test that uses the installed package.



\- \*\*Scope creep\*\*

&nbsp; - \*Risk\*: Attempting to add analytical/OLAP or DevAssist integration into v0.2.

&nbsp; - \*Mitigation\*: Keep such items in `backlog.md`; treat analytical support as `\[P2]` for this release.



---



\## 8. Notes \& Decisions



\- 2025-12-15 – v0.2 will remain \*\*strictly read-only\*\*; no admin/ETL tools will be introduced.

\- 2025-12-15 – Competing Datasphere MCP server(s) are acknowledged, but this project’s differentiator is \*\*AI-first, safe, minimal core\*\* over maximum tool count.

\- 2025-12-15 – DevAssist/Sethi integration is explicitly tracked in `backlog.md` and not in v0.2 scope.

\- 2025-12-15 – Default licensing for v0.2 remains \*\*MIT\*\*, at least unless a later decision changes this; existing v0.1 MIT license remains irrevocable.

\- 2025-12-15 – Tentative PyPI/CLI name for this project is `sap-datasphere-mcp-server`; final choice will be confirmed before packaging.

\- 2025-12-15 – v0.2 will reuse the \*\*Claude Code\*\* sanity scenario from v0.1 as a regression test, plus new tests for metadata/profiling/diagnostics.



