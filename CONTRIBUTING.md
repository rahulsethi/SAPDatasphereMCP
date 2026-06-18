# Contributing to SAP Datasphere MCP Server

Thanks for considering a contribution. This guide explains how to set up,
make changes, and submit pull requests.

## Quick start

```bash
git clone https://github.com/rahulsethi/SAPDatasphereMCP.git
cd SAPDatasphereMCP
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # or `source .venv/bin/activate`
pip install -e ".[dev]"
pytest
```

Python **3.11+** is required.

## Project layout

See the architecture diagram in [README.md](README.md) for the high-level picture. The boot path is
`transports/stdio_server.py → server.create_server() → tools/registry.register_all()`.

## Where to add a new tool

1. Decide its category: `connectivity`, `catalog`, `query`, `discover`,
   `profile`, `summarize`, or `governance`.
2. Add the async function to `src/sap_datasphere_mcp/tools/tasks.py` (the
   implementation lives there).
3. Add the registration entry in the matching `src/sap_datasphere_mcp/tools/<category>.py`
   facade module with per-tool metadata via `@tool_metadata`.
4. Add an output schema in `src/sap_datasphere_mcp/schemas/` if the return
   shape isn't already covered.
5. Add a test in `tests/` (use the `MockDatasphereClient` for fast offline
   coverage).

## Coding style

- `ruff check src/ tests/` — must pass.
- Functions returning JSON-serializable dicts only; no dataclasses across the
  tool boundary.
- Errors return `{"ok": false, "error": {...}, "meta": {...}}`; never raise to
  the MCP layer.
- Read-only contract is sacrosanct — no write tools targeting tenant admin
  surfaces. This is a hard guarantee for the 1.x line.

## Tests

- `pytest tests/` should remain green at every commit.
- Add tests for every new tool, alias, and prompt.
- Live-tenant integration is via `examples/smoke_*.py` only (never in `tests/`).

## License

Contributions are accepted under the **PolyForm Noncommercial 1.0.0** license
(applies to v1.0+). No CLA required; contributors retain copyright. See
[`COMMERCIAL_LICENSING.md`](COMMERCIAL_LICENSING.md) for how the dual model
works.

## Releasing

Releases are cut by the maintainer. Releases tag the `main` branch (`v1.2.3`)
and publish automatically to PyPI + GitHub Releases via GitHub Actions.

## Reporting bugs

Open an issue at https://github.com/rahulsethi/SAPDatasphereMCP/issues.

For security-sensitive reports, use GitHub's private security advisory flow
rather than a public issue.
