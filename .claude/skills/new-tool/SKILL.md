---
name: new-tool
description: Scaffold a new SAP Datasphere MCP tool across all four required layers (client method, business-logic function, @server.tool wrapper, example + test) following project conventions. Use when adding a new datasphere_* tool.
disable-model-invocation: true
---

# new-tool — scaffold a SAP Datasphere MCP tool

Adding a tool to this server is a fixed 4-layer ritual. Do all four, in order, and
keep the conventions in `CLAUDE.md`. Never skip the example or the test.

## Inputs to gather first

- **Tool name** — `datasphere_<verb>` (e.g. `datasphere_list_views`).
- **What it returns** — rows (`QueryResult`), metadata, or a summary dict.
- **Which Datasphere API** — catalog vs. consumption (relational / analytical), and
  whether it needs a new HTTP call or can reuse an existing `DatasphereClient` method.
- **Row-returning?** — if yes, which cap applies (`max_rows_preview`, `max_rows_query`,
  `max_rows_profile`, `max_rows_analytical`, `max_search_results`).

## Layer 1 — `src/sap_datasphere_mcp/client.py`

Only if a new HTTP call is needed. Add an `async def` on `DatasphereClient`. Rules:

- Get the token via `await self.oauth.get_access_token()`.
- Build URL candidates from `self._catalog_prefixes()` or `self._consumption_prefixes()`
  — never hardcode `/dwc` or `/datasphere`. Include both URL-shape variants the way
  `preview_asset_data` / `query_relational` do.
- Call `self._get_with_fallback(urls=..., headers=..., params=..., allow_top_fallback=...)`.
- Escape OData key literals: `space_id.replace("'", "''")`.
- Return a typed model from `models.py` (`Space`, `Asset`, `QueryResult`) where it fits.
- Bump the `# Version: vN` header comment.

## Layer 2 — module-level `async def` in `src/sap_datasphere_mcp/tools/tasks.py`

This is the business logic + guardrails layer (NOT yet the MCP wrapper). Rules:

- Honor `mock_mode` (use the `_Mock*` client path already in the file).
- Clamp any row argument with `_cap_int(value, cap)` and report `cap_applied` in `meta`.
- On failure return the `_make_error(code, message, details)` shape — keep messages
  short and LLM-friendly. Do not leak credentials or full tokens.
- Return plain JSON-serializable dicts/lists.

## Layer 3 — `@server.tool(...)` wrapper inside `register_tools(server)` (same file)

- Add near the other `@server.tool(...)` registrations (~line 1700+).
- `name="datasphere_<verb>"`, a one-line `description` written for an LLM caller.
- The wrapper just validates/forwards args to the Layer-2 function and returns its result.

## Layer 4 — example + test

- `examples/demo_mcp_<verb>.py` — mirror an existing `demo_mcp_*.py` (they construct the
  server / call the tool end-to-end).
- `tests/test_<area>.py` — add a test that runs with `DATASPHERE_MOCK_MODE` set so it needs
  no live tenant. Mirror the closest existing test module.

## Verify

```powershell
pip install -e ".[dev]"   # if not already
ruff check . ; ruff format .
pytest -q
```

Report which files you created/edited and confirm the new tool shows up in `register_tools`.
