<!-- SAP Datasphere MCP Server -->
<!-- File: docs/v1.0/ImplementationTracker_v1.0.md -->
<!-- Version: v1 (1.0) -->
<!-- Status: in-flight / 1.0 cut date 2026-07-13 -->

# Implementation Tracker — v1.0

> ⚠️ **As-shipped reconciliation — added 2026-07-01 (post-dates this doc).** Where this tracker disagrees with the shipped code / root `LICENSE` / `CHANGELOG.md`, **the code is authoritative**:
>
> - **A5 / K1 (License):** shipped as **Business Source License 1.1 (BSL 1.1)** → Apache 2.0 on 2029-01-01, **not** PolyForm Noncommercial.
> - **A1 (PyPI name):** rename **reverted** — distribution kept as **`mcp-sap-datasphere-server`**; a `mcp-sap-datasphere-server` console-script alias was added (`uvx mcp-sap-datasphere-server`). Ignore `sap-datasphere-mcp` as a package/install target below.
> - **mTLS:** `DATASPHERE_OAUTH_MTLS_CERT`/`_KEY` are documented posture only — **not yet wired into `auth.py`** (roadmap).
>
> Corrected as-shipped docs live in root `CHANGELOG.md`, `LICENSE`, and `public_docs/`.

Companion to `ProjectPlan_v1.0.md` (the *what & why*) and `Decisions_v1.0.md`
(the *because*). This tracker is the *did we do it*. Each row maps to a
concrete unit of work with status and verification notes.

Status legend:

- [x] **Done** — landed in `main`, tests cover the surface, doc updated.
- [/] **In flight** — partially landed; remaining work called out in the row.
- [ ] **Open** — not yet started.

---

## Section A — Distribution, license, packaging

| # | Item | Status | Notes |
|---|---|---|---|
| A1 | Rename PyPI dist `mcp-sap-datasphere-server` → `sap-datasphere-mcp` | [x] | `pyproject.toml:project.name`. v0.3.x dist still resolvable in `__init__._resolve_version` for upgraders. |
| A2 | Bump version to `1.0.0` | [x] | `pyproject.toml`, `src/.../__init__.py` fallback constant. |
| A3 | Python floor → `>=3.11` | [x] | `pyproject.toml:requires-python`. |
| A4 | `mcp[cli]>=1.25.0`, `python-dotenv`, `jsonschema` deps | [x] | `pyproject.toml:dependencies`; resolved at 1.27.2 locally. |
| A5 | LICENSE: MIT → PolyForm Noncommercial 1.0.0 | [x] | `LICENSE`; matches sibling SAPBDCMCP. |
| A6 | `COMMERCIAL_LICENSING.md` at repo root | [x] | Short pointer; long-form lives in `public_docs/COMMERCIAL_LICENSING.md`. |
| A7 | `CONTRIBUTING.md` | [x] | First-pass; sibling-aligned. |
| A8 | `MANIFEST.in` | [x] | Includes `public_docs/`, excludes `docs/` (developer docs). |
| A9 | `.env.example` | [x] | All v1.0 env vars documented inline. |
| A10 | `.editorconfig` | [x] | Mirrors sibling. |
| A11 | `set-datasphere-env.example.ps1` retained | [x] | Windows-friendly template (added in v0.3.1, kept). |
| A12 | `pyproject.toml` URLs (`Homepage`, `Repository`, `Family`, `Changelog`) | [x] | Surface family link to SAPBDCMCP. |

## Section B — Source code: structure & boot path

| # | Item | Status | Notes |
|---|---|---|---|
| B1 | `server.py` factory (shared by both transports) | [x] | `create_server()` returns FastMCP. |
| B2 | `__main__.py` (`python -m sap_datasphere_mcp`) | [x] | |
| B3 | `tools/_metadata.py` — central tool registry, 24 entries | [x] | One ToolMetadata per tool; iter / by_legacy_name helpers. |
| B4 | `tools/_gated.py` — policy + audit + redaction interceptor | [x] | `functools.wraps` preserves signature for FastMCP introspection. |
| B5 | `tools/_aliases.py` — built from metadata | [x] | 16 legacy aliases. |
| B6 | `tools/{connectivity,catalog,query,discover,profile,summarize,governance}.py` | [x] | Facade modules with BINDINGS lists. |
| B7 | `tools/registry.py` — `register_all(server)` | [x] | Registers 24 canonical + 16 aliases = 40 tool entries. |
| B8 | `tools/tasks.py` left untouched | [x] | 22 async impls remain the single source of behavior. Deeper split deferred per ADR-011. |

## Section C — Governance modules

| # | Item | Status | Notes |
|---|---|---|---|
| C1 | `audit.py` — JSONL audit log | [x] | Disabled by default; OS-appropriate default path. |
| C2 | `policy.py` — API Policy v4/2026 gate | [x] | `is_strict`, `permits`, `disclosure`. |
| C3 | `policy_evidence.py` — static disclosure data | [x] | Deployment tiers + verifiable claims list. |
| C4 | `redaction.py` — secret/PII scrubbing | [x] | Enabled by default; conservative pattern set. |
| C5 | `tools/governance.api_policy_check` (NEW) | [x] | Returns full disclosure dict. |
| C6 | `tools/governance.audit_tail` (NEW) | [x] | Capped at 500; no-ops when audit disabled. |
| C7 | Audit record schema documented | [x] | Section 9.1 of ProjectPlan; mirrored in Architecture §4. |

## Section D — MCP whitespace plays

| # | Item | Status | Notes |
|---|---|---|---|
| D1 | MCP tool annotations (`readOnlyHint`/`idempotentHint`/etc.) on all 24 tools | [x] | Best-effort dict; degrades gracefully on older SDKs. |
| D2 | Structured `outputSchema` per tool | [/] | Deferred to a 1.0.x point release — schemas under `src/.../schemas/` to be added incrementally. Tracking issue: TBD. |
| D3 | MCP Prompts (5): `profile_dataset`, `audit_space`, `explain_analytical_model`, `compare_assets`, `find_data_about_topic` | [x] | First SAP MCP server to ship prompts. |
| D4 | MCP Resources (4): `datasphere://space/{id}` + 3 nested patterns | [x] | First SAP MCP server to ship resources. |
| D5 | Cursor-based pagination on list_* tools | [/] | Tools still accept `top`/`skip` per OData; opaque cursors deferred to 1.0.x. |

## Section E — API path migration

| # | Item | Status | Notes |
|---|---|---|---|
| E1 | Default `client.py` path order: modern first, legacy fallback | [x] | `_catalog_prefixes` and `_consumption_prefixes` rebuilt. |
| E2 | `DATASPHERE_API_PATH_LEGACY=1` to force legacy order | [x] | Documented in `.env.example` and `public_docs/MIGRATION.md`. |
| E3 | `DatasphereClient.path_mode` property for diagnostics | [x] | Returns `"modern"` or `"legacy"`. |
| E4 | Legacy fallback works on 404/405 | [x] | Inherited from existing `_get_with_fallback`. |

## Section F — Transports

| # | Item | Status | Notes |
|---|---|---|---|
| F1 | `stdio_server.py` uses `server.create_server()` | [x] | Plus `--version` / `--help` short flags. |
| F2 | `http_server.py` uses `server.create_server()` | [x] | Plus `_maybe_apply_bearer` for optional bearer auth. |
| F3 | `DATASPHERE_MCP_BEARER_TOKEN` wired through | [x] | Best-effort against MCP SDK; logs warn if no auth hook. |

## Section G — Plugins

| # | Item | Status | Notes |
|---|---|---|---|
| G1 | `plugins/registry.py` unchanged | [x] | Already supported entry-point modules at v0.3. |
| G2 | `npx:`/`uvx:`/`cmd:` subprocess upstreams + trust list | [/] | Tracked for 1.0.x. Sibling-style subprocess upstream is meaningful only if we have community plugins requesting it. |

## Section H — Distribution channels

| # | Item | Status | Notes |
|---|---|---|---|
| H1 | `npx-wrapper/package.json` (Node 18+) | [x] | `@rahulsethi/sap-datasphere-mcp`. |
| H2 | `npx-wrapper/bin/sap-datasphere-mcp.js` | [x] | Probes uvx → pipx → python3; forwards signals + stdio. |
| H3 | `npx-wrapper/README.md` | [x] | Short note + Claude Desktop snippet. |
| H4 | PyPI upload | [ ] | Manual step on release tag — not done in this PR. |
| H5 | npm publish | [ ] | Manual step on release tag — not done in this PR. |
| H6 | GitHub Release notes assembly | [ ] | After PR lands. |

## Section I — CI & DX

| # | Item | Status | Notes |
|---|---|---|---|
| I1 | `.github/workflows/ci.yml` — pytest matrix (Linux/macOS/Win × 3.11/3.12/3.13) | [x] | + ruff + build + npx-wrapper smoke. |
| I2 | Build verification (`python -m build`) | [/] | Wheel built locally during `pip install -e .` (1.0.0). Standalone `python -m build` run pending. |
| I3 | `ruff check` baseline | [ ] | Open — first ruff run not gated yet; CI will catch regressions. |

## Section J — Documentation

| # | Item | Status | Notes |
|---|---|---|---|
| J1 | `docs/v1.0/ProjectPlan_v1.0.md` | [x] | 20 sections + appendix. |
| J2 | `docs/v1.0/Architecture_v1.0.md` | [x] | 12 sections, ~2,300 words. Layered ASCII diagram, boot path, facade pattern, interceptor chain, prompts/resources, path migration, config model, error shape, plugins, concurrency, compat matrix. |
| J3 | `docs/v1.0/Decisions_v1.0.md` | [x] | 12 ADRs (ADR-001..ADR-012) in Nygard format. |
| J4 | `docs/v1.0/ImplementationTracker_v1.0.md` | [x] | This file. |
| J5 | `docs/v1.0/TestPrompts_v1.0.md` | [ ] | Open. Lift v0.3 patterns; one prompt per category. |
| J6 | Root `README.md` rewrite for 1.0 | [x] | Family section, MCP Gateway recommendation, 24-tool catalog reference. |
| J7 | Root `CHANGELOG.md` 1.0 entry | [x] | Added / Changed / Deprecated / Removed / Fixed / Licensing / Deferred / Migration. |
| J8 | `public_docs/README.md` | [x] | Marketing-friendly landing. |
| J9 | `public_docs/INSTALLATION.md` | [x] | uvx / pip / npx / Cursor / Claude Desktop. |
| J10 | `public_docs/QUICKSTART.md` | [x] | 5-minute path. |
| J11 | `public_docs/TOOLS.md` | [x] | All 24 tools + prompts + resources. |
| J12 | `public_docs/MIGRATION.md` | [x] | 22-row rename table + env-var additions + troubleshooting. |
| J13 | `public_docs/SAP_API_POLICY.md` | [x] | DSAG context, 3-tier deployment guide, tool classification table. |
| J14 | `public_docs/COMMERCIAL_LICENSING.md` | [x] | Friendly path; placeholder `<contact@your-org-here>` for maintainer to fill before publish. |
| J15 | `docs/SAP_API_POLICY.md` (developer-facing mirror) | [ ] | Optional; `public_docs/SAP_API_POLICY.md` is the user-facing source. |
| J16 | Architecture image refresh | [ ] | Existing `docs/Architecture.png` is pre-1.0; refresh deferred. |

## Section K — Family alignment with SAPBDCMCP

| # | Item | Status | Notes |
|---|---|---|---|
| K1 | License alignment (PolyForm) | [x] | A5. |
| K2 | Tool naming alignment (`<product>_<category>_<verb>`) | [x] | All 24 v1.0 names follow the pattern. |
| K3 | Env-var alignment for shared concepts (`*_MOCK_MODE`, `*_VERIFY_TLS`, `*_PLUGINS`, `*_AUDIT_ENABLED`, `*_AUDIT_LOG_PATH`, `*_API_POLICY_STRICT`, `*_PLUGIN_TRUST`) | [x] | Names mirror sibling with `DATASPHERE_` prefix. |
| K4 | `tools/` split into per-category package | [x] | Facade-only — implementations remain in `tasks.py` per ADR-011. |
| K5 | CHANGELOG section taxonomy (Added / Changed / Deprecated / Removed / Fixed / Licensing / Deferred / Migration) | [x] | New 1.0 entry uses the full taxonomy. |
| K6 | npx-wrapper distribution | [x] | Section H. |
| K7 | `## Family` link in root README, both directions | [/] | Done on our side. PR in SAPBDCMCP to add reciprocal link is **open / to be filed**. |
| K8 | Cross-link to SAPBDCMCP in `pyproject.toml [project.urls]` | [x] | `Family = "https://github.com/rahulsethi/SAPBDCMCP"`. |

## Section L — Testing

| # | Item | Status | Notes |
|---|---|---|---|
| L1 | All 21 v0.3.1 tests still green | [x] | No regression. |
| L2 | New: `test_v1_registry.py` — registry, governance tools, prompts/resources wiring, redaction, policy, alias log-once | [x] | 13 new tests; total suite at **34 green**. |
| L3 | End-to-end `create_server()` smoke test | [x] | `test_create_server_smoke`. |
| L4 | Manual: HTTP transport + bearer auth | [ ] | Manual verification deferred to pre-release gate. |
| L5 | Manual: all 5 prompts driven from Claude Desktop against a real tenant | [ ] | Pre-release gate. |
| L6 | Manual: 4 Resource URIs resolve in MCP Inspector | [ ] | Pre-release gate. |
| L7 | Path migration: live-tenant test with `DATASPHERE_API_PATH_LEGACY=0` and `=1` | [ ] | Manual; recorded in release notes. |

---

## Pre-release gates (must be green before tagging `v1.0.0`)

- [ ] All entries in this tracker either Done or explicitly marked *Deferred to 1.0.x* with a tracking note.
- [ ] `pytest` green on all CI matrix cells.
- [ ] `ruff check` clean.
- [ ] `python -m build` produces a wheel that installs cleanly into a scratch venv.
- [ ] `pip install sap-datasphere-mcp` against a TestPyPI upload works (token rotation pending).
- [ ] `npx -y @rahulsethi/sap-datasphere-mcp --wrapper-version` smoke against TestPyPI dist.
- [ ] Live-tenant smoke on each of the 5 MCP Prompts; transcripts saved to release notes.
- [ ] `COMMERCIAL_LICENSING.md` contact placeholder filled in.
- [ ] Sibling SAPBDCMCP `## Family` link PR opened.
- [ ] Tag `v1.0.0` cut; GitHub Release published with built artifacts.

## What deliberately ships AFTER 1.0

Per `ProjectPlan_v1.0.md` §2.2 and `Decisions_v1.0.md` ADR-009 / ADR-011:

- Per-tool `outputSchema` files under `src/.../schemas/` (D2)
- Opaque cursor pagination (D5)
- `npx:`/`uvx:`/`cmd:` subprocess plugin upstreams (G2)
- Deeper `tasks.py` decomposition into per-category logic modules
- Data Product tools — the SAP-endorsed BDC agent surface
- SAP Knowledge Graph integration
- Lineage / data quality first-class tools
- Anthropic MCP registry application
- Joule-for-Datasphere passthrough (if a public API emerges)
