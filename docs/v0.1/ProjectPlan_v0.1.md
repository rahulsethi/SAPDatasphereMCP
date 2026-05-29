

---



\## 2. `ProjectPlan.md`



```markdown

\# Project Plan – SAP Datasphere MCP Server



This document describes the development plan, phases, and tasks for building the SAP Datasphere MCP Server.



---



\## Objectives



1\. Build a \*\*standalone MCP server\*\* that exposes SAP Datasphere via tools/resources.

2\. Start with \*\*read‑only\*\* metadata and data access (safe by default).

3\. Keep the core \*\*transport‑agnostic\*\* (MCP stdio first, HTTP optional later).

4\. Design the tool set so it can be easily consumed by \*\*DevAssist/Sethi\*\* Tool/Connector agents.



---



\## Phases \& Milestones



\### Phase A – Project Setup \& Skeleton



\*\*Goal:\*\* Have a runnable MCP server skeleton with no real SAP calls yet.



\*\*Tasks:\*\*



\- \[ ] Initialize Python project (`pyproject.toml`, virtualenv/poetry).

\- \[ ] Define base package structure under `src/sap\_datasphere\_mcp`.

\- \[ ] Add core dependencies:

&nbsp; - `mcp` SDK

&nbsp; - HTTP client (`httpx` or `requests`)

&nbsp; - `pydantic` or `dataclasses`

\- \[ ] Implement `transports/stdio\_server.py` with:

&nbsp; - Basic `ping` or `health\_check` tool.

\- \[ ] Verify MCP server works with a sample host (e.g., Claude Desktop).



\*\*Deliverable:\*\*  

A minimal MCP server that runs and exposes a trivial tool.



---



\### Phase B – Connectivity \& Metadata (Spaces + Catalog)



\*\*Goal:\*\* Authenticate to Datasphere and explore spaces and catalog assets.



\*\*Tools (planned):\*\*



\- `datasphere.get\_connection\_status`

\- `datasphere.list\_spaces`

\- `datasphere.get\_space\_details`

\- `datasphere.list\_space\_assets`

\- `datasphere.search\_assets`

\- `datasphere.get\_asset\_details`

\- `datasphere.explain\_asset\_semantics` (LLM‑friendly schema summary)



\*\*Tasks:\*\*



\- \[ ] Implement `config.py` for environment‑based settings (URLs, credentials).

\- \[ ] Implement `auth.py`:

&nbsp; - OAuth2 client credentials

&nbsp; - Token caching + refresh

\- \[ ] Implement `client.py` methods for:

&nbsp; - Listing spaces

&nbsp; - Listing assets within a space

&nbsp; - Fetching asset metadata

\- \[ ] Implement tool handlers under `tools/spaces.py` and `tools/catalog.py`.

\- \[ ] Add basic unit tests with mocked HTTP.

\- \[ ] Manual integration test against a real Datasphere tenant.



\*\*Deliverable:\*\*  

MCP server can list spaces and assets and describe their metadata using live SAP Datasphere.



---



\### Phase C – Data Access (Preview + Queries)



\*\*Goal:\*\* Allow controlled data access via preview and parameterized queries.



\*\*Tools (planned):\*\*



\- `datasphere.preview\_asset\_data`

\- `datasphere.query\_relational\_data`

\- `datasphere.query\_analytical\_model`



\*\*Tasks:\*\*



\- \[ ] Extend `client.py` to call Datasphere consumption APIs:

&nbsp; - Relational endpoints

&nbsp; - Analytical endpoints

\- \[ ] Implement OData type → friendly type mapping in `models.py`.

\- \[ ] Implement preview method with:

&nbsp; - Row limit (default small, e.g. 20)

&nbsp; - Column limit if needed

\- \[ ] Implement query methods with:

&nbsp; - `$select`, `$filter`, `$orderby`, `$top`, `$skip`

&nbsp; - Safe defaults \& hard caps

\- \[ ] Implement tool handlers in `tools/data.py`.

\- \[ ] Add tests for query building \& shape of responses.

\- \[ ] Manual tests on real tables/views/analytical models.



\*\*Deliverable:\*\*  

MCP tools can retrieve sample data and run basic queries in a predictable, safe manner.



---



\### Phase D – Hardening, Mock Mode, Packaging



\*\*Goal:\*\* Make the server robust, testable, and easy to adopt.



\*\*Tasks:\*\*



\- \[ ] Implement error handling and friendly error messages:

&nbsp; - Auth failures

&nbsp; - Missing spaces/assets

&nbsp; - Invalid queries

\- \[ ] Add structured logging (tool name, API calls, timings, result counts).

\- \[ ] Implement `DATASPHERE\_MOCK\_MODE` for:

&nbsp; - Returning synthetic spaces/assets/data for demos/tests.

\- \[ ] Clean up packaging:

&nbsp; - Console entry point: `sap-datasphere-mcp`

&nbsp; - PyPI‑ready structure (optional)

\- \[ ] Add usage examples in `README.md`.



\*\*Deliverable:\*\*  

Production‑ready, read‑only Datasphere MCP server with good diagnostics.



---



\### Phase E – DevAssist/Sethi Integration (Future)



\*\*Goal:\*\* Use this MCP server as the Datasphere connector inside DevAssist/Sethi.



\*\*Tasks (later, in DevAssist project):\*\*



\- Define a `DatasphereToolAgent` (or similar) that:

&nbsp; - Calls MCP tools for spaces/catalog/queries.

&nbsp; - Stores useful metadata in DevAssist memory/RAG.

\- Add configuration guidance:

&nbsp; - How to point DevAssist at the MCP server.

\- Add example workflows:

&nbsp; - “Inspect Datasphere models used in this project”

&nbsp; - “Generate a query over Datasphere for this use case”



\*\*Deliverable:\*\*  

DevAssist can use this MCP server without code changes on the Datasphere side.



---



\## Effort Estimate (Rough)



\- Phase A: 1–1.5 days

\- Phase B: 3–4 days

\- Phase C: 4–5 days

\- Phase D: 2–3 days



Total for a solid, read‑only MCP server: \*\*~12–16 dev‑days\*\*.



Phase E depends on DevAssist timelines and is owned by that project.



