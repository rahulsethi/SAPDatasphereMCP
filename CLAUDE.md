# CLAUDE.md — SAP Datasphere MCP Server

Project memory for Claude Code. Read this before making changes.

## What this is

An MCP (Model Context Protocol) server that exposes SAP Datasphere catalog and
consumption APIs as tools and resources. Package name `mcp-sap-datasphere-server`,
import name `sap_datasphere_mcp`. Python 3.10+, built with hatchling.

Console entrypoint: `sap-datasphere-mcp` → `sap_datasphere_mcp.transports.stdio_server:main`.

## Layout

- `src/sap_datasphere_mcp/`
  - `config.py` — `DatasphereConfig.from_env()`; all `DATASPHERE_*` env vars, row caps, cache settings, TLS toggle, mock mode.
  - `auth.py` — `OAuthClient`, client-credentials flow (HTTP Basic), in-memory token cache with expiry leeway and an async lock to prevent token stampedes.
  - `client.py` — `DatasphereClient`; catalog + consumption REST calls with `_get_with_fallback` (tries `/dwc/...` then `/datasphere/...` URL variants, falls back on 404/405).
  - `cache.py` — `TTLCache` for metadata.
  - `models.py` — `Space`, `Asset`, `QueryResult` dataclasses.
  - `tools/tasks.py` — **the single place** business logic lives. ~30 MCP tools wired up in `register_tools(server)`.
  - `plugins/registry.py` — optional plugin loader via `DATASPHERE_PLUGINS`; plugin failures must never crash the core server.
  - `transports/stdio_server.py`, `transports/http_server.py` — FastMCP entrypoints.
- `tests/` — pytest + pytest-asyncio. Use `DATASPHERE_MOCK_MODE` to avoid live calls.
- `examples/` — `demo_*` and `smoke_*` scripts that exercise tools end-to-end.
- `docs/v0.1/`, `docs/v0.2/` — project plans / implementation trackers.

## Conventions

- Every source file starts with a `# File:` / `# Version: vN` header comment. Bump the version comment when you meaningfully change a file.
- Adding a new MCP tool touches **four layers**, in this order:
  1. `DatasphereClient` method in `client.py` (the actual HTTP call, with URL fallback).
  2. A module-level `async def` in `tools/tasks.py` (business logic, error shaping, row caps).
  3. A `@server.tool(...)` wrapper inside `register_tools()` in `tools/tasks.py`.
  4. An `examples/demo_mcp_*.py` and a test in `tests/`.
- Tool names are prefixed `datasphere_*`. Errors use the `_make_error(code, message, details)` shape — keep them LLM-friendly.
- Respect the config guardrails: clamp row counts to `max_rows_*` caps, honor `verify_tls` and `mock_mode` on every code path.
- Never hardcode the URL prefix — go through `_catalog_prefixes()` / `_consumption_prefixes()` so both `/dwc` and `/datasphere` tenants work.

## Commands

```powershell
# Install (editable, with dev deps)
pip install -e ".[dev]"

# Run tests
pytest

# Lint / format
ruff check .
ruff format .

# Run the server over stdio
sap-datasphere-mcp
```

## Secrets & config

- Credentials come from env vars (`DATASPHERE_TENANT_URL`, `DATASPHERE_OAUTH_TOKEN_URL`, `DATASPHERE_CLIENT_ID`, `DATASPHERE_CLIENT_SECRET`). Legacy aliases `DATASPHERE_OAUTH_CLIENT_ID/SECRET` are still honored.
- `set-datasphere-env.ps1` and `.env*` are git-ignored and hold real secrets — **never** read, print, or commit them. `set-datasphere-env.example.ps1` is the safe template.

## Versioning / release

Version lives in `pyproject.toml`. Keep `CHANGELOG.md` and the README in sync when bumping. Recent line: v0.3.0 → v0.3.1.

---

# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
