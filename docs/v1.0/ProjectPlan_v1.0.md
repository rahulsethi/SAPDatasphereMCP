<!-- SAP Datasphere MCP Server -->
<!-- File: docs/v1.0/ProjectPlan_v1.0.md -->
<!-- Version: v1 -->
<!-- Status: design / awaiting review -->
<!-- Author: Rahul Sethi -->
<!-- Date: 2026-05-30 -->

# SAP Datasphere MCP Server — v1.0 Project Plan

> ⚠️ **As-shipped reconciliation — added 2026-07-01 (post-dates this design doc).** Several v1.0 decisions changed during execution. Where this document disagrees with the shipped code / root `LICENSE` / `CHANGELOG.md`, **the code is authoritative**:
>
> - **License:** shipped under the **Business Source License 1.1 (BSL 1.1)**, which converts to Apache 2.0 on 2029-01-01 — **not** PolyForm Noncommercial. The noncommercial-free / commercial-paid *intent* is unchanged.
> - **PyPI distribution name:** kept as **`mcp-sap-datasphere-server`** — the planned rename to `sap-datasphere-mcp` was reverted (that short name is an unrelated community package). A `mcp-sap-datasphere-server` console-script alias was added, so install with **`uvx mcp-sap-datasphere-server`** / **`pip install mcp-sap-datasphere-server`**. Any `pip install`/`uvx`/`pipx sap-datasphere-mcp` command below is obsolete — `sap-datasphere-mcp` is only the console-script/command name.
> - **mTLS (Tier C):** documented posture only — `DATASPHERE_OAUTH_MTLS_CERT`/`_KEY` are **not yet wired into the OAuth token flow** in `auth.py` (roadmap, not implemented).
>
> Corrected as-shipped docs live in root `CHANGELOG.md`, `LICENSE`, and `public_docs/`.

## 1. Context

`SAPDatasphereMCP` shipped v0.1.0 in late 2025 and reached v0.3.1 on 2026-05-30 as a cleanup release. Between January 2026 (v0.3.0 shipped) and today, three forces have shifted the ground under the project and now converge on a natural graduation moment.

### 1.1 What changed in the SAP world

- **SAP API Policy v4/2026** (effective **2026-06-09**) — Section 2.2.2 prohibits using SAP APIs for "interaction or integration with (semi-)autonomous or generative AI systems that plan, select, or execute sequences of API calls" *except through SAP-endorsed pathways*. Enforcement reality is contested by DSAG, but the policy is the framing every enterprise procurement team will use against community MCP servers for the next 18 months. ([SAP API Policy v.4.2026a](https://help.sap.com/doc/sap-api-policy/latest/en-US/API_Policy_latest.pdf), [CIO](https://www.cio.com/article/4166172/dsag-criticizes-saps-new-api-policy.html))
- **API path migration** (Wave 2025.19) — `/api/v1/dwc/*` deprecated in favor of `/api/v1/datasphere/...`. Catalog moved further to `/api/v1/datasphere/consumption/catalog/*`. Old paths supported through **March 2027**. All four endpoints used by v0.3.1 are on the deprecated tree. ([SAP Community — Using Technical User in Datasphere Consumption APIs](https://community.sap.com/t5/technology-blog-posts-by-sap/using-technical-user-in-sap-datasphere-consumption-apis-client-credentials/ba-p/14218919))
- **SAP + Anthropic at Sapphire 2026** (2026-05-12) — Claude is the primary reasoning engine for Joule across SAP. 224 Claude-powered Joule agents announced. SAP now ships two official MCP surfaces: **Integration Suite MCP Gateway** (governed exposure of any SAP API as MCP tools with metering) and **HANA Cloud native MCP**. Neither covers Datasphere directly — that whitespace is still open. ([SAP News](https://news.sap.com/2026/05/sap-anthropic-to-bring-claude-sap-business-ai-platform/), [SAP Community — POV 3](https://community.sap.com/t5/technology-blog-posts-by-sap/pov-3-using-integration-suite-as-your-governed-mcp-server-platform-part-3-4/ba-p/14328366))
- **Business Data Cloud (BDC) is the new umbrella** — Datasphere + SAC are delivered via BDC. **Data Products** + **Delta Sharing** are SAP's officially endorsed agent-facing data surface and the sanctioned replacement for the API patterns Section 2.2.2 targets. ([SAP Architecture Center](https://architecture.learning.sap.com/docs/ref-arch/f5b6b597a6/1))

### 1.2 What changed in the competitive landscape

- **`MarioDeFelipe/sap-datasphere-mcp`** has emerged as the primary community competitor — 29★, **45 tools**, v1.2.1, PyPI + npm + uv distribution, streamable HTTP with bearer auth, aligned to Datasphere wave 2026.10. Ships database user CRUD (`create_database_user`, `reset_database_user_password`) — an enterprise foot-gun that we can use as a positioning lever. ([repo](https://github.com/MarioDeFelipe/sap-datasphere-mcp))
- **Same maintainer also ships `MarioDeFelipe/sap-bdc-mcp-server`** — so he is flanking our sibling repo `SAPBDCMCP` too. A unified family front is a competitive necessity, not just polish.
- **Convergent patterns nobody in the SAP MCP space has adopted** (Mario included): MCP tool annotations (`readOnlyHint`/`idempotentHint`/`destructiveHint`), `outputSchema` + structured content, MCP **Prompts**, MCP **Resources** (URI-addressable catalog), cursor pagination. Databricks-MCP ships 8 prompts; no SAP server ships any. Pure whitespace.
- **No SAP-official Datasphere MCP exists.** Official SAP MCPs are limited to CAP, Fiori (open-ux-tools), UI5, UI5 Web Components, MDK. The Datasphere slot is unclaimed and the policy + Sapphire announcements suggest SAP will not ship one themselves in the near term — they want Integration Suite Gateway + native HANA MCP to cover this.

### 1.3 What changed in our sibling repo

`rahulsethi/SAPBDCMCP` reached v0.2.0 on 2026-05-27. It has structurally diverged from `SAPDatasphereMCP` v0.3.1 along multiple axes:

| Axis | SAPBDCMCP v0.2.0 | SAPDatasphereMCP v0.3.1 |
|---|---|---|
| License | PolyForm Noncommercial 1.0.0 | MIT |
| Build backend | setuptools | hatchling |
| Python floor | 3.11 | 3.10 |
| `mcp` pin | `>=1.25.0` | `>=1.2.0` |
| Tool naming | `bdc_<category>_<verb>` | `datasphere_<verb>` |
| `tools/` layout | per-category package (11 files) | single 1931-line file |
| Audit / policy / redaction | present (`audit.py`, `policy.py`, `redaction.py`) | absent |
| Per-tool risk metadata | yes (`tools/_gated.py`, `tools/metadata.py`) | no |
| Mock mode | first-class | none |
| Plugin loader | Python + `npx:`/`uvx:`/`cmd:` subprocess + trust list | entry-point only |
| `npx-wrapper` distribution | yes | no |
| Cross-link to sibling | none | none |

Neither repo currently advertises the other.

### 1.4 The graduation moment

Three breaking changes converge naturally:

1. **API path migration** — mechanical breaking change driven by SAP.
2. **Distribution rename** — `mcp-sap-datasphere-server` → `sap-datasphere-mcp` (matches console script, matches sibling pattern `sap-bdc-mcp`).
3. **Tool naming overhaul** — `datasphere_<verb>` → `datasphere_<category>_<verb>` to align with sibling.
4. **License change** — MIT → PolyForm Noncommercial 1.0.0 to match sibling.

Shipping any one as a 0.x release wastes the lift. Bundling them as **1.0** lets the release carry one coherent narrative — *API Policy v4 aligned, Claude/Sapphire era, family-aligned with SAPBDCMCP* — that pre-1.0 framing cannot. v1.0 is also the natural moment to apply for the Anthropic MCP registry and pitch the project as enterprise-grade.

---

## 2. Goals & non-goals

### 2.1 Goals (1.0 must deliver)

- **G1. API Policy v4/2026 alignment** — credible, documented posture (governance code + disclosure + recommended Integration Suite Gateway deployment).
- **G2. API path migration** — clients on the new `/api/v1/datasphere/...` tree by default with backward-compat toggle for legacy tenants.
- **G3. Family alignment with SAPBDCMCP** — license, tool naming convention, env var shape, `tools/` layout, audit/policy/redaction patterns, Python floor, dependency pins, cross-links.
- **G4. MCP whitespace plays** — tool annotations, `outputSchema`/structured content, MCP Prompts (≥5), MCP Resources (URI-addressable catalog), cursor pagination.
- **G5. Read-only enterprise positioning** — preserve "no write tools" stance; lean on it as a security/procurement differentiator vs Mario.
- **G6. SemVer 1.0 stability commitment** — public tool surface + env var contract is stable through the 1.x line; deprecations only via documented aliases.

### 2.2 Non-goals (explicitly deferred)

- **Data Product tools** — SAP-endorsed surface but adds significant scope. Defer to 1.1.
- **SAP Knowledge Graph integration** — interesting but Datasphere-side maturity is early. Defer.
- **Lineage / data quality first-class tools** — defer; partial coverage already via `get_asset_metadata`.
- **BDC Delta Sharing resolver** — primarily a BDC concern; sibling repo will own it.
- **Anthropic MCP registry application** — pursue post-1.0 once the surface is stable.
- **Joule-for-Datasphere passthrough** — no public API found; defer.
- **Task Chain API write tools** — violates read-only posture; out of scope permanently for this project.
- **Database user CRUD** — explicit non-goal; foot-gun that Mario ships and we deliberately don't.
- **`tools/tasks.py` business-logic refactor** beyond splitting by category — defer further extraction (`core.py`, etc.) to 1.1+.

### 2.3 Out of scope for this plan (sibling-repo work)

- Updating `SAPBDCMCP` to add cross-links, fix the unresolved `<<<<<<< HEAD` merge marker in `pyproject.toml` on `main`, and align its build backend / Python floor with this repo. Tracked separately in the sibling.

---

## 3. Decisions ratified in brainstorm

| # | Decision | Value | Rationale |
|---|---|---|---|
| D1 | Release version | **1.0.0** | Three breaking changes converge; SemVer demands major bump |
| D2 | Headline framing | **"API Policy aligned, Family aligned"** | Coherent narrative; pre-empts Mario; gives security teams ammunition |
| D3 | License | **PolyForm Noncommercial 1.0.0** | Matches sibling; commercial moat; consistent family story |
| D4 | Tool naming | **`datasphere_<category>_<verb>` full rename** | Matches sibling; deprecation aliases for 1.x minor; drop in 1.2 |
| D5 | Governance port | **Full port** of audit + policy + redaction + per-tool risk metadata from sibling | Adapted to Datasphere read-only context |

---

## 4. Defaults baked in (flag at spec review to override)

These low-stakes decisions are encoded with my best call. Each is reversible during review.

| # | Decision | Default | Alternative |
|---|---|---|---|
| F1 | Distribution name | Rename `mcp-sap-datasphere-server` → `sap-datasphere-mcp` | Keep current name |
| F2 | Python floor | Bump 3.10 → 3.11 | Stay on 3.10 |
| F3 | `mcp` SDK pin | Bump `>=1.2.0` → `>=1.25.0` | Stay loose |
| F4 | Build backend | **Keep hatchling**; track sibling migration to hatchling as a follow-up in SAPBDCMCP | Switch us to setuptools |
| F5 | Add deps | `python-dotenv>=1.0.1`, `jsonschema>=4.20.0` | Skip |
| F6 | Distribution channels | PyPI + npm (`@rahulsethi/sap-datasphere-mcp`) + uvx instructions | PyPI only |
| F7 | `npx-wrapper/` | Add for parity with sibling and Mario | Skip |
| F8 | MCP Prompts shipped | Five: `profile_dataset`, `audit_space`, `explain_analytical_model`, `compare_assets`, `find_data_about_topic` | Different list |
| F9 | MCP Resources URI scheme | `datasphere://space/{id}`, `datasphere://space/{id}/asset/{name}`, `datasphere://space/{id}/asset/{name}/schema`, `datasphere://space/{id}/asset/{name}/sample` | Different scheme |
| F10 | Cross-repo link | Add README "Family" section to both repos with reciprocal link | Skip |
| F11 | CHANGELOG section taxonomy | Adopt sibling's: Added / Changed / Deprecated / Removed / Fixed / **Licensing** / **Deferred** / **Migration** | Stay basic |
| F12 | OAuth mTLS option | Optional path via `DATASPHERE_OAUTH_MTLS_CERT` + `_KEY` env vars (RFC 8705) | Skip for 1.0 |

---

## 5. Architecture

### 5.1 Package layout after 1.0

```
SAPDatasphereMCP/
├── pyproject.toml                  # name: sap-datasphere-mcp, Python>=3.11, hatchling
├── README.md                        # rewritten; family section; architecture diagram
├── CHANGELOG.md                     # Added/Changed/Deprecated/Removed/Fixed/Licensing/Deferred/Migration
├── LICENSE                          # PolyForm Noncommercial 1.0.0
├── CONTRIBUTING.md                  # NEW — port from sibling
├── COMMERCIAL_LICENSING.md          # NEW — explains commercial license offer
├── MANIFEST.in                      # NEW
├── .editorconfig                    # NEW
├── .env.example                     # NEW — POSIX env file (sibling parity)
├── set-datasphere-env.example.ps1   # existing (kept for Windows users)
├── .github/workflows/               # NEW — CI: pytest + ruff + build
├── .cursor/                         # NEW — Cursor IDE MCP config example
├── npx-wrapper/                     # NEW — Node bootstrap → uvx
├── src/sap_datasphere_mcp/
│   ├── __init__.py                  # __version__ = "1.0.0"
│   ├── __main__.py                  # NEW — `python -m sap_datasphere_mcp` entry
│   ├── audit.py                     # NEW — JSONL audit log
│   ├── auth.py                      # extended — mTLS path
│   ├── cache.py                     # unchanged
│   ├── client.py                    # path migration; structured-error returns
│   ├── config.py                    # extended — new env vars
│   ├── models.py                    # extended — DataProductDescriptor (for 1.1 prep)
│   ├── policy.py                    # NEW — API Policy gating
│   ├── policy_evidence.py           # NEW — policy disclosure data
│   ├── redaction.py                 # NEW — secret/PII scrubbing
│   ├── prompts/                     # NEW — MCP Prompts package
│   │   ├── __init__.py
│   │   ├── profile_dataset.py
│   │   ├── audit_space.py
│   │   ├── explain_analytical_model.py
│   │   ├── compare_assets.py
│   │   └── find_data_about_topic.py
│   ├── resources/                   # NEW — MCP Resources package
│   │   ├── __init__.py
│   │   └── catalog_resources.py
│   ├── plugins/registry.py          # extended — subprocess npx:/uvx:/cmd: + trust list
│   ├── tools/
│   │   ├── __init__.py              # marker
│   │   ├── _aliases.py              # NEW — old-name → new-name deprecation shim
│   │   ├── _gated.py                # NEW — risk-gated decorator
│   │   ├── _metadata.py             # NEW — per-tool risk metadata
│   │   ├── connectivity.py          # NEW — 5 tools
│   │   ├── catalog.py               # NEW — 4 tools (file name reused; old empty file deleted in 0.3.1)
│   │   ├── query.py                 # NEW — 3 tools
│   │   ├── discover.py              # NEW — 3 tools
│   │   ├── profile.py               # NEW — 2 tools
│   │   ├── summarize.py             # NEW — 4 tools
│   │   ├── governance.py            # NEW — 1 new tool
│   │   └── registry.py              # NEW — registers everything; replaces `tasks.register_tools`
│   ├── server.py                    # NEW — FastMCP factory shared by both transports
│   ├── transports/
│   │   ├── stdio_server.py
│   │   └── http_server.py           # extended — optional bearer auth header
│   └── schemas/                     # NEW — bundled JSON Schemas for outputSchema
├── tests/
├── examples/
├── fixtures/                        # NEW — sample tenant payloads for offline tests
└── docs/
    ├── Architecture.md              # rewritten with 1.0 diagram
    ├── SAP_API_POLICY.md            # NEW — policy disclosure
    ├── MIGRATION_v0.3_to_v1.0.md    # NEW — breaking-change guide
    ├── backlog.md
    ├── Extensions.md
    ├── README.md
    ├── CHANGELOG.md                 # pointer (existing)
    ├── v0.1/, v0.2/, v0.3/, v1.0/
```

The single 1931-line `tools/tasks.py` is decomposed into seven per-category modules + a small registry. The 20 async tool implementations move with minimal logic changes; the registration plumbing is rewritten.

### 5.2 Boot path after 1.0

```
console script `sap-datasphere-mcp`
  → transports.stdio_server:main
    → server.create_server()              # NEW factory
      → tools.registry.register_all()     # replaces tasks.register_tools
        → tools.{connectivity,catalog,query,discover,profile,summarize,governance}.register()
      → prompts.register(mcp)             # NEW
      → resources.register(mcp)           # NEW
      → plugins.registry.register_plugins(mcp)   # extended
    → mcp.run(transport="stdio")
```

The HTTP transport (`transports.http_server:main`) uses the same `create_server()` factory and adds optional bearer auth + `/health`.

---

## 6. Tool catalog (v1.0)

### 6.1 Canonical names and mapping

24 tools after rename (22 ported + 2 new). Old names remain registered as deprecation aliases through 1.1, dropped in 1.2.

| Category | New name (1.0) | Old name (0.3.x) | Annotations |
|---|---|---|---|
| **connectivity** | `datasphere_connectivity_ping` | `datasphere_ping` | readOnly, idempotent |
| connectivity | `datasphere_connectivity_diagnostics` | `datasphere_diagnostics` | readOnly |
| connectivity | `datasphere_connectivity_tenant_info` | `datasphere_get_tenant_info` | readOnly, idempotent |
| connectivity | `datasphere_connectivity_whoami` | `datasphere_get_current_user` | readOnly, idempotent |
| connectivity | `datasphere_connectivity_plugins_status` | `datasphere_plugins_status` | readOnly |
| **catalog** | `datasphere_catalog_list_spaces` | `datasphere_list_spaces` | readOnly, idempotent |
| catalog | `datasphere_catalog_list_assets` | `datasphere_list_assets` | readOnly, idempotent |
| catalog | `datasphere_catalog_get_asset` | `datasphere_get_asset_metadata` | readOnly, idempotent |
| catalog | `datasphere_catalog_list_columns` | `datasphere_list_columns` | readOnly, idempotent |
| catalog | `datasphere_catalog_space_overview` | `datasphere_space_summary` | readOnly, idempotent |
| **query** | `datasphere_query_preview` | `datasphere_preview_asset` | readOnly |
| query | `datasphere_query_relational` | `datasphere_query_relational` | readOnly |
| query | `datasphere_query_analytical` | `datasphere_query_analytical` | readOnly |
| **discover** | `datasphere_discover_assets` | `datasphere_search_assets` | readOnly |
| discover | `datasphere_discover_assets_with_column` | `datasphere_find_assets_with_column` | readOnly |
| discover | `datasphere_discover_assets_by_column` | `datasphere_find_assets_by_column` | readOnly |
| **profile** | `datasphere_profile_schema` | `datasphere_describe_asset_schema` | readOnly |
| profile | `datasphere_profile_column` | `datasphere_profile_column` | readOnly |
| **summarize** | `datasphere_summarize_asset` | `datasphere_summarize_asset` | readOnly |
| summarize | `datasphere_summarize_space` | `datasphere_summarize_space` | readOnly |
| summarize | `datasphere_summarize_column_profile` | `datasphere_summarize_column_profile` | readOnly |
| summarize | `datasphere_summarize_compare_assets` | `datasphere_compare_assets_basic` | readOnly |
| **governance** | `datasphere_governance_api_policy_check` | *(NEW)* | readOnly, idempotent |
| **governance** | `datasphere_governance_audit_tail` | *(NEW — optional, behind env flag)* | readOnly |

All 24 tools are explicitly `readOnly`. None are `destructive`. None mutate tenant state.

**Note on the `space_summary` / `summarize_space` distinction.** v0.1 shipped `datasphere_space_summary` (a quick catalog-tier overview: counts by type, sample list). v0.3 added `datasphere_summarize_space` (a deterministic, cached, structured summary intended for LLM consumption). Both ship in 1.0 under their new category names — `datasphere_catalog_space_overview` (quick) and `datasphere_summarize_space` (deterministic). A future 1.1 may unify them; flagged in `docs/backlog.md`.

### 6.2 Tool annotations

Every tool gets the MCP 2025-03-26 annotations:

```python
@mcp.tool(
    name="datasphere_catalog_list_spaces",
    description="List Datasphere spaces visible to the OAuth client.",
    annotations=ToolAnnotations(
        title="List Datasphere spaces",
        readOnlyHint=True,
        idempotentHint=True,
        destructiveHint=False,
        openWorldHint=True,
    ),
)
```

This lets Claude Desktop and other hosts skip confirmation prompts for our read-only tools — a real UX upgrade.

### 6.3 `outputSchema` + structured content

Every tool that returns structured data declares an `outputSchema` (JSON Schema). The schemas live in `src/sap_datasphere_mcp/schemas/` and are exported per tool. Tools return `(structuredContent, fallback_text)` tuples per the MCP spec.

### 6.4 Cursor-based pagination

`datasphere_catalog_list_spaces`, `datasphere_catalog_list_assets`, `datasphere_discover_*` accept an opaque `cursor` parameter. Cursors are base64-encoded JSON containing the underlying OData `$skip` value plus a fingerprint of the query parameters; rejected if the fingerprint doesn't match (prevents `$skip` smuggling across different queries).

### 6.5 Deprecation alias layer

`tools/_aliases.py` registers every old `datasphere_<verb>` name as a thin wrapper around its new `datasphere_<category>_<verb>` implementation. Each alias call emits a one-time-per-process structured log:

```
{"event":"tool_alias_used","old":"datasphere_list_spaces","new":"datasphere_catalog_list_spaces","ts":"..."}
```

Aliases are present through 1.1 and removed in 1.2. The README migration guide tells users how to update Claude Desktop configs.

---

## 7. MCP Resources

Four URI patterns expose catalog content as MCP Resources, addressable without tool calls:

| URI | Returns |
|---|---|
| `datasphere://space/{space_id}` | Space metadata: id, name, description, last-updated, asset counts by type |
| `datasphere://space/{space_id}/asset/{asset_name}` | Asset metadata: type, labels, exposure flags (relational/analytical), description |
| `datasphere://space/{space_id}/asset/{asset_name}/schema` | Column list (via `$metadata` when possible, sample-fallback when not) |
| `datasphere://space/{space_id}/asset/{asset_name}/sample` | Up to `DATASPHERE_RESOURCE_SAMPLE_ROWS` (default 5) rows — strictly capped |

Resources are listed via `resources/list` and served via `resources/read`. URI patterns are also returned in tool responses (e.g. `datasphere_catalog_list_assets` includes the resource URI per asset) so a host can pre-load context.

No SAP MCP server currently exposes Resources. First-in-class.

---

## 8. MCP Prompts

Five prompt templates shipped under `prompts/`:

| Prompt name | Args | Purpose |
|---|---|---|
| `profile_dataset` | `space_id`, `asset_name` | End-to-end profile: schema + sample + per-column profile + summary. Single user-friendly walk. |
| `audit_space` | `space_id` | Walk every asset in a space, capture metadata, flag stale assets, summarize ownership/exposure. |
| `explain_analytical_model` | `space_id`, `asset_name` | For an analytical asset, return dimensions/measures/hierarchies/relationships in plain English. |
| `compare_assets` | `space_a`, `asset_a`, `space_b`, `asset_b` | Structural comparison: column overlap, type mismatches, row-count delta, naming differences. |
| `find_data_about_topic` | `topic` (free text), optional `space_ids` | Multi-space discover + summarize to surface candidate assets for an analytic question. |

Each prompt is an assembled message sequence that calls the relevant 1.0 tools in order. Prompts are listed via `prompts/list` and rendered via `prompts/get`.

No SAP MCP server currently ships prompts. First-in-class.

---

## 9. Governance layer (ported from sibling)

### 9.1 `audit.py`

Per-tool-call structured JSONL log. Default path `~/.cache/sap-datasphere-mcp/audit.log`; overridable via `DATASPHERE_AUDIT_LOG_PATH`. Disabled by default; enable via `DATASPHERE_AUDIT_ENABLED=1`.

Record shape:

```json
{
  "ts": "2026-05-30T15:42:01.314Z",
  "tool": "datasphere_query_relational",
  "duration_ms": 412,
  "outcome": "ok",
  "args_fingerprint": "sha256:abc123…",
  "rows_returned": 47,
  "tenant_url_hash": "sha256:def456…",
  "sub": "oauth-client-id:b3650",
  "policy_strict": false
}
```

Argument values are NOT logged in plaintext — only a deterministic fingerprint. Tenant URL is hashed. The OAuth `sub` is logged in clear (it's already a public client identifier).

### 9.2 `policy.py` + `policy_evidence.py`

A simple gate that classifies each tool against the SAP API Policy v4/2026 surface:

- **Permitted always** — connectivity tools, governance tools.
- **Permitted under client-credentials** — catalog, query, discover, profile, summarize. The whole core surface.
- **Gated** — none in 1.0 (we have no destructive tools).

If `DATASPHERE_API_POLICY_STRICT=1`, the server refuses any future tool tagged as gated. With the 1.0 surface, strict mode is a no-op but it's wired so 1.1+ tool additions inherit the gate.

`datasphere_governance_api_policy_check` returns:

```json
{
  "policy_version": "v4.2026a",
  "deployment_posture": "community_oauth_client_credentials",
  "recommended_path": "Integration Suite MCP Gateway",
  "tools_by_class": { "permitted_always": [...], "permitted_under_cc": [...], "gated": [] },
  "audit_enabled": true,
  "redaction_enabled": true,
  "mtls_enabled": false,
  "disclosure_url": "https://github.com/rahulsethi/SAPDatasphereMCP/blob/main/docs/SAP_API_POLICY.md"
}
```

### 9.3 `redaction.py`

Regex-based scrubbing applied to tool returns before serialization. Default patterns:

- OAuth client secrets (long `[A-Za-z0-9+/=]{40,}` strings appearing in unexpected fields)
- Tokens / JWTs (`eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+`)
- Email addresses (configurable; off by default — too aggressive for legitimate enterprise data)
- Bearer headers in echoed error payloads

Per-tool opt-out via the `_metadata.py` decorator (e.g. `datasphere_connectivity_tenant_info` deliberately surfaces redacted-but-recognizable forms of URLs).

### 9.4 Per-tool risk metadata

Every tool decorated with `@tool_metadata(...)` declaring:

- `category`: connectivity / catalog / query / discover / profile / summarize / governance
- `risk_level`: low / medium / high (all current tools are `low`)
- `data_class`: none / metadata / sample-data / full-data
- `policy_class`: permitted_always / permitted_under_cc / gated
- `output_schema`: reference to JSON schema file
- `aliases`: list of legacy names

Drives MCP annotations, README per-tool risk table, audit log enrichment, and policy gate.

---

## 10. API path migration

### 10.1 The change

`DatasphereClient` switches default base path from `/api/v1/dwc/` to `/api/v1/datasphere/`. Catalog endpoints additionally move from `/catalog/` to `/consumption/catalog/`.

| v0.3.1 | v1.0 default |
|---|---|
| `GET /api/v1/dwc/catalog/spaces` | `GET /api/v1/datasphere/consumption/catalog/spaces` |
| `GET /api/v1/dwc/catalog/spaces/{space}/assets` | `GET /api/v1/datasphere/consumption/catalog/spaces/{space}/assets` |
| `GET /api/v1/dwc/consumption/relational/{space}/{asset}` | `GET /api/v1/datasphere/consumption/relational/{space}/{asset}` |
| `GET /api/v1/dwc/consumption/analytical/{space}/{asset}` | `GET /api/v1/datasphere/consumption/analytical/{space}/{asset}` |

### 10.2 Backward compatibility

`DATASPHERE_API_PATH_LEGACY=1` (default `0`) reverts to the `/api/v1/dwc/` tree. Documented as a one-line escape hatch for tenants on older waves; flagged in the migration guide as something to remove by March 2027.

`DatasphereClient` exposes a `path_mode` property so diagnostics and policy_check can surface which path tree the server is currently hitting.

### 10.3 Testing

Add a recorded-cassette pytest using `respx` (or simple monkeypatched httpx) that runs every endpoint method in both `path_mode="modern"` and `path_mode="legacy"` against fixture payloads. No live-tenant dependency.

---

## 11. Family alignment with SAPBDCMCP

| Aspect | Action |
|---|---|
| License | Relicense MIT → PolyForm Noncommercial 1.0.0; add `COMMERCIAL_LICENSING.md` matching sibling |
| Distribution name | Rename `mcp-sap-datasphere-server` → `sap-datasphere-mcp` |
| Python floor | Bump 3.10 → 3.11 |
| `mcp` SDK pin | Bump `>=1.2.0` → `>=1.25.0` |
| Tool naming | `datasphere_<category>_<verb>` with deprecation aliases |
| Env var prefix | Stay on `DATASPHERE_*` (correct per product) |
| Env var alignment for shared knobs | Adopt sibling names where conceptually identical: `DATASPHERE_MOCK_MODE`, `DATASPHERE_VERIFY_TLS` (already), `DATASPHERE_PLUGINS` (already), `DATASPHERE_AUDIT_ENABLED` (new), `DATASPHERE_AUDIT_LOG_PATH` (new), `DATASPHERE_API_POLICY_STRICT` (new), `DATASPHERE_PLUGIN_TRUST` (new) |
| `tools/` layout | Per-category package matching sibling |
| Governance modules | Port `audit.py`, `policy.py`, `policy_evidence.py`, `redaction.py`, `_gated.py`, `_metadata.py` |
| Mock mode | Adopt `DATASPHERE_MOCK_MODE=1` with sibling-style demo dataset (already partially present in 0.3.x — formalize) |
| Plugin loader | Extend `plugins/registry.py` to support `npx:`/`uvx:`/`cmd:` subprocess upstreams and a trust list (`DATASPHERE_PLUGIN_TRUST`) — mirror sibling exactly |
| `npx-wrapper/` | Add for parity |
| CHANGELOG sections | Adopt sibling taxonomy: Added / Changed / Deprecated / Removed / Fixed / Licensing / Deferred / Migration |
| README polish | Lift sibling structure: enterprise positioning paragraph, ASCII architecture diagram, per-tool risk table, dual install (pip + npx + uvx), Claude Desktop + Cursor + LibreChat snippets, "Family" section linking to SAPBDCMCP |
| CONTRIBUTING.md, MANIFEST.in, .editorconfig, .github/workflows, .cursor/, .env.example | Port from sibling |
| Cross-link | Both READMEs gain a `## Family` section: SAPDatasphereMCP links to SAPBDCMCP and vice-versa; same one-paragraph blurb |

---

## 12. Packaging & distribution

- **PyPI**: `pip install sap-datasphere-mcp`
- **npm**: `@rahulsethi/sap-datasphere-mcp` via `npx-wrapper/` (small Node shim that runs `uvx sap-datasphere-mcp`)
- **uvx**: `uvx sap-datasphere-mcp` works out of the box once on PyPI
- **GitHub Release**: wheel + sdist attached, release notes mirror `CHANGELOG.md` for 1.0

`pyproject.toml` excerpt after change:

```toml
[project]
name = "sap-datasphere-mcp"
version = "1.0.0"
description = "SAP Datasphere MCP server — read-only, API Policy v4/2026 aligned"
readme = "README.md"
requires-python = ">=3.11"
license = { file = "LICENSE" }

dependencies = [
  "mcp[cli]>=1.25.0",
  "httpx>=0.27.0",
  "pydantic>=2.7.0",
  "python-dotenv>=1.0.1",
  "jsonschema>=4.20.0",
]

[project.scripts]
sap-datasphere-mcp = "sap_datasphere_mcp.transports.stdio_server:main"
```

---

## 13. Documentation

- **README.md (root)** — full rewrite. Sections: tagline + "Latest release: v1.0.0", **Family** (link to SAPBDCMCP), Why this exists / read-only positioning vs Mario, **API Policy v4/2026 disclosure** (one paragraph, link to docs), ASCII architecture diagram, Install (pip + npx + uvx), Configure (env table), Run, Tool catalog v1.0 (table with risk + annotations), MCP Resources, MCP Prompts, Migration from v0.3.x, Versioning, License + Commercial.
- **docs/SAP_API_POLICY.md** — new. Same shape as sibling. Lists each tool's policy class and how the deployment can be hardened (mTLS, Integration Suite Gateway).
- **docs/MIGRATION_v0.3_to_v1.0.md** — new. Step-by-step: new pip name, new tool names (mapping table), env var changes (none mandatory; one new optional set), API path toggle if needed.
- **docs/Architecture.md** — rewritten. Layered diagram showing: MCP host → FastMCP server → registry → category modules → DatasphereClient → policy/audit/redaction interceptors → Datasphere REST.
- **docs/backlog.md** — updated. Items moved to "Deferred for 1.1+" section: Data Products tools, Knowledge Graph integration, lineage tools, Delta Sharing resolver, Joule passthrough, Anthropic registry application.
- **docs/v1.0/ProjectPlan_v1.0.md** — this file.
- **docs/v1.0/ImplementationTracker_v1.0.md** — to be created during implementation.
- **docs/v1.0/TestPrompts_v1.0.md** — to be created during implementation; one prompt per category for human QA.

---

## 14. Breaking changes

| # | What | Migration |
|---|---|---|
| B1 | Package name `mcp-sap-datasphere-server` → `sap-datasphere-mcp` | `pip uninstall mcp-sap-datasphere-server && pip install sap-datasphere-mcp` |
| B2 | All 22 tool names changed | Aliases through 1.1 (with deprecation log); update Claude Desktop / Cursor configs by 1.2 |
| B3 | License MIT → PolyForm Noncommercial 1.0.0 (v1.0+) | Existing 0.3.1 MIT downloads remain MIT. New downloads governed by PolyForm. Commercial use requires separate license — contact maintainer. |
| B4 | Python floor 3.10 → 3.11 | Upgrade interpreter |
| B5 | Default API path `/api/v1/dwc/*` → `/api/v1/datasphere/*` | Set `DATASPHERE_API_PATH_LEGACY=1` if still on a wave that requires the old paths (rare; auto-detection possible in 1.1) |
| B6 | `tools.tasks.register_tools` removed (was the boot entry from 0.3.x) | Replaced by `tools.registry.register_all`. Users calling this directly (probably none) must update import. |

A row-by-row migration table is also reproduced in `docs/MIGRATION_v0.3_to_v1.0.md`.

---

## 15. Verification plan

### 15.1 Automated

- **Existing 21-test pytest suite** must remain green throughout. Each rename PR runs the full suite.
- **Add tests** for: every new MCP Prompt (assert prompt structure), every MCP Resource (assert URI → content), `outputSchema` validation on every tool return shape, deprecation alias coverage (every old name resolves to its new tool), API path mode toggle (every endpoint method in both modes against fixture cassettes), audit log emission (write + JSON shape), redaction (each pattern → expected scrub), policy gate (gated tool refused under strict mode).
- **Target test count: ≥60** (up from 21). Coverage gate at 85% on `src/sap_datasphere_mcp/`.
- **CI**: `.github/workflows/ci.yml` runs `pytest`, `ruff check`, `python -m build`, and a quick `mcp inspect` smoke against the stdio server.

### 15.2 Manual / live

- Run all 5 MCP Prompts end-to-end against a real tenant via Claude Desktop. Capture output for the release notes.
- Verify every MCP Resource resolves and renders in MCP Inspector.
- Run the legacy alias log warning visibly in Claude Desktop with `DATASPHERE_VERBOSE_DEPRECATIONS=1`.
- mTLS path verified once against an IAS instance configured with cert-based client_credentials.

### 15.3 Pre-release gates

- [ ] All breaking changes documented in `MIGRATION_v0.3_to_v1.0.md` with command-line examples.
- [ ] `LICENSE` is PolyForm 1.0.0; `COMMERCIAL_LICENSING.md` present.
- [ ] README's first 200 lines pass a "could a procurement reviewer approve this in 5 minutes?" read-through.
- [ ] SAPBDCMCP README updated with the reciprocal Family link (sibling PR opened separately).
- [ ] Tag `v1.0.0` cut, wheel + sdist uploaded to PyPI, npx wrapper version bumped, GitHub Release published.

---

## 16. Timing & sequencing

The June 9 API Policy date is **not** a hard technical block on our OAuth client_credentials usage (per research: enforcement is policy-only, the security patch on June 9 specifically targets ODP-via-RFC). But the optics matter, and the path migration alone is enough to justify a defensive interim.

Proposed sequence:

| Date | Release | Scope |
|---|---|---|
| **2026-06-08** | **0.3.2 hotfix** | Path migration only (`DATASPHERE_API_PATH_LEGACY` env added, default `0`). One commit, one test addition, ~4-hour effort. Lands ahead of the policy date so existing 0.3.x users get the new path automatically. Stays MIT. |
| 2026-06-09 → 2026-07-13 | 1.0 work | Family alignment, governance port, MCP whitespace, tool rename, license change, docs rewrite |
| **2026-07-13** | **1.0.0** | Full plan as designed |
| 2026-07-20 | sibling SAPBDCMCP v0.3.0 | Cross-link landed, build backend migration to hatchling, merge-conflict cleanup in pyproject.toml |
| 2026-08-15+ | 1.1 | Data Products tools (deferred from 1.0), additional whitespace plays based on early 1.0 feedback |

A 0.3.2 hotfix is recommended because it's near-zero-effort and removes any "but the path is deprecated" objection during the longer 1.0 cycle.

---

## 17. Risks & mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| MarioDeFelipe ships first with similar features | Med | Low | Lean on read-only + family-alignment + first-in-class Prompts/Resources differentiation; even if surfaces overlap, the positioning narrative differs |
| Section 2.2.2 enforced against community OAuth clients | Low | High | Recommend Integration Suite Gateway deployment in README; document policy posture; mTLS option ready |
| PolyForm relicense scares away community contributors | Low-Med | Med | Sibling went PolyForm without losing contributors; documented commercial offer is clear and friendly |
| Tool rename breaks every existing Claude Desktop config | Cert | Low | Aliases through 1.1; one-time-per-process deprecation log; clear migration guide |
| `tools/` split introduces regressions in tool behavior | Med | Med | Behavior of every async function is unchanged — only file location and registration plumbing move. Full pytest run on every commit. |
| `outputSchema` adoption uncovers latent bugs in tool return shapes | Med | Low | Schemas are generated from observed returns first, then tightened. Tests cover both shape and content. |
| March 2027 deprecation of legacy `dwc` path missed | Low | Med | `path_mode="legacy"` use logged at warn level; CHANGELOG migration section reminds users; we'll cut 2.0 by Q1 2027 to remove the toggle. |
| Anthropic MCP spec evolves underneath us | Low | Med | Pin `mcp[cli]>=1.25.0,<2.0`; reassess at 1.x.0 |

---

## 18. Open questions to resolve at spec review

1. **0.3.2 hotfix** — do we want the interim path-migration patch (Section 16), or jump straight to 1.0?
2. **MCP Prompts list** — five proposed. Add / remove / rename any?
3. **MCP Resources URI scheme** — proposed `datasphere://space/{id}/asset/{name}/...`. Acceptable, or prefer a different shape (e.g., flatter `datasphere://asset/{space}/{name}`)?
4. **npx package scope** — `@rahulsethi/sap-datasphere-mcp` proposed. Different scope (e.g., your own org name)?
5. **Mock mode dataset** — formalize the existing v0.2 mock or design a new one with more coverage (5 spaces / 30 assets)?
6. **Audit log default path** — `~/.cache/sap-datasphere-mcp/audit.log` proposed. OS-appropriate alternative (`%LOCALAPPDATA%` on Windows)?
7. **Commercial license terms** — what should `COMMERCIAL_LICENSING.md` say? Defer to maintainer; suggest mirroring sibling.
8. **Sibling-repo PR** — do we open the cross-link PR ourselves, or hand it to the maintainer?

---

## 19. What this plan deliberately is not

- It is not an implementation step list. That comes next (`ImplementationTracker_v1.0.md` during build).
- It is not a marketing brief. Release-comms copy comes during the 1.0 release cycle.
- It is not a final SAP-policy legal opinion. The policy disclosure documents posture and best-effort compliance; legal sign-off from SAP-side enterprise customers is their own due diligence.

---

## 20. Appendix — Sources

- SAP API Policy v.4.2026a — [help.sap.com](https://help.sap.com/doc/sap-api-policy/latest/en-US/API_Policy_latest.pdf)
- SAP Datasphere External Access Overview — [community.sap.com](https://community.sap.com/t5/technology-blog-posts-by-sap/sap-datasphere-external-access-overview-apis-cli-and-sql/ba-p/14078591)
- SAP Datasphere & SAC availability via BDC — [community.sap.com](https://community.sap.com/t5/technology-blog-posts-by-sap/announcement-sap-datasphere-and-sap-analytics-cloud-availability-via-sap/ba-p/14140920)
- Using Technical User in Datasphere Consumption APIs — [community.sap.com](https://community.sap.com/t5/technology-blog-posts-by-sap/using-technical-user-in-sap-datasphere-consumption-apis-client-credentials/ba-p/14218919)
- Managing Data Products Using REST APIs — [help.sap.com](https://help.sap.com/docs/SAP_DATASPHERE/e4059f908d16406492956e5dbcf142dc/59768ad8c8054d2db92fdf545b0a2485.html)
- SAP + Anthropic Sapphire 2026 — [news.sap.com](https://news.sap.com/2026/05/sap-anthropic-to-bring-claude-sap-business-ai-platform/)
- POV 3: Integration Suite as governed MCP server — [community.sap.com](https://community.sap.com/t5/technology-blog-posts-by-sap/pov-3-using-integration-suite-as-your-governed-mcp-server-platform-part-3-4/ba-p/14328366)
- DSAG criticizes SAP's new API policy — [cio.com](https://www.cio.com/article/4166172/dsag-criticizes-saps-new-api-policy.html)
- New SAP API policy AI clause — [theregister.com](https://www.theregister.com/2026/04/29/new_sap_api_policy_provokes/)
- MarioDeFelipe/sap-datasphere-mcp — [github.com](https://github.com/MarioDeFelipe/sap-datasphere-mcp)
- MarioDeFelipe/sap-bdc-mcp-server — [github.com](https://github.com/MarioDeFelipe/sap-bdc-mcp-server)
- "SAP has two MCPs" — [Mario Defelipe, Medium](https://medium.com/@mario.defelipe/sap-has-two-mcps-one-you-cant-use-one-you-shouldn-t-445ce6e409b9)
- marianfoo/sap-ai-mcp-servers — [github.com](https://github.com/marianfoo/sap-ai-mcp-servers)
- SAP Official MCP Servers list — [likweitan.github.io](https://likweitan.github.io/sap-mcp-servers-official/)
- MCP Tool Annotations — [blog.modelcontextprotocol.io](https://blog.modelcontextprotocol.io/posts/2026-03-16-tool-annotations/)
- FastMCP — structured outputs & outputSchema — [gofastmcp.com](https://gofastmcp.com/servers/tools)
- SAP BTP Security: client-credentials with IAS mTLS — [community.sap.com](https://community.sap.com/t5/technology-blog-posts-by-sap/sap-btp-security-how-to-realize-client-credentials-flow-with-it-2-mtls/ba-p/13564508)
- PolyForm Noncommercial 1.0.0 — [polyformproject.org](https://polyformproject.org/licenses/noncommercial/1.0.0/)
- Sibling repo SAPBDCMCP — [github.com/rahulsethi/SAPBDCMCP](https://github.com/rahulsethi/SAPBDCMCP)
