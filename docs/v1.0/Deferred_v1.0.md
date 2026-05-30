<!-- SAP Datasphere MCP Server -->
<!-- File: docs/v1.0/Deferred_v1.0.md -->
<!-- Version: v1 (1.0) -->
<!-- Last updated: 2026-05-30 -->

# Deferred — v1.0

The single, canonical list of work that v1.0 explicitly does **not** ship,
the target release for each item, and *why* it was deferred. Cross-linked
from `ProjectPlan_v1.0.md §2.2`, `Decisions_v1.0.md` (relevant ADRs), and
`ImplementationTracker_v1.0.md` (status rows).

Three reasons an item lands here, in decreasing severity:

1. **Risk** — the change is correct in spirit but the blast radius (refactor
   scope, regression risk, scope creep) is too large for a graduation release.
2. **Maturity** — the upstream SAP surface, the MCP spec feature, or the
   tooling around it isn't stable enough yet to commit to a public contract.
3. **Sequencing** — the item depends on something else that has to land first
   (a sibling-repo PR, a TestPyPI rotation, a live-tenant validation).

If the world changes — SAP ships a new endpoint, an ADR is reversed, a
competitor moves — items can be pulled forward. Edit this file in the PR
that does it; don't let the doc drift behind the code.

---

## Status legend

- **1.0.x** — pencil-in for a patch release inside the 1.0 line (no breaking
  changes; no SemVer bump needed).
- **1.1** — pencil-in for the next minor; visible scope for the next planning
  pass.
- **post-1.0 / unscheduled** — wanted but not slotted; revisit on demand.
- **manual pre-release gate** — a one-shot operational step that has to run
  before the v1.0.0 git tag is cut; not a code change.

---

## Section 1 — Code & schema deferrals

| ID | Item | Target | Why deferred | References |
|---|---|---|---|---|
| DEF-001 | Per-tool `outputSchema` JSON Schemas under `src/sap_datasphere_mcp/schemas/` | 1.0.x | Schemas should be generated from real observed returns, not invented; let the 1.0 surface stabilize for ~2-4 weeks of live use first. The infrastructure (`MANIFEST.in` ships the folder; tool metadata has a hook) is already in place. | `ProjectPlan_v1.0.md §6.3`, `ImplementationTracker_v1.0.md D2` |
| DEF-002 | Opaque cursor-based pagination on `datasphere_catalog_list_*` and `datasphere_discover_*` | 1.0.x | Current implementation accepts OData-native `top` / `skip` and that has worked for v0.3.x; cursor encoding is a quality-of-life win, not a correctness fix. Spec design needs one more review (cursor format, fingerprint validation, error on stale cursor). | `ProjectPlan_v1.0.md §6.4`, `ImplementationTracker_v1.0.md D5` |
| DEF-003 | `npx:`, `uvx:`, `cmd:` subprocess plugin upstreams in `plugins/registry.py` + `DATASPHERE_PLUGIN_TRUST` allowlist | 1.0.x | The Python entry-point plugin path covers every plugin we know about today; subprocess upstreams are a sibling-feature-parity item with no current community demand. Land when a real plugin asks for it. | `ProjectPlan_v1.0.md §11`, `ImplementationTracker_v1.0.md G2` |
| DEF-004 | Deeper decomposition of `tools/tasks.py` (1931 lines) into per-category logic modules | 1.1 | The 1.0 facade refactor renames the surface without moving implementations — minimal regression risk for a release that already changes license + package name + tool names. Logic-level extraction is its own ~1-2 week task. | `Decisions_v1.0.md ADR-011`, `ImplementationTracker_v1.0.md B8` |
| DEF-005 | Deduplicate `_parse_bool_env` (`config.py`) vs `_env_flag` (`tasks.py`, several modules) | 1.0.x | Pure cleanup; touching it now risks subtle env-parsing behavior changes during a release that already moves a lot. Cheap to do in a focused PR after 1.0 lands. | `ProjectPlan_v0.3.1` plan file (carried forward) |
| DEF-006 | Simplify MCP SDK compat shim in `transports/http_server.py` (`_run_server`, `_maybe_apply_bearer`) | 1.1 | We pin `mcp[cli]>=1.25.0` at 1.0 but still want to tolerate small variation across 1.25→1.30+. After two or three SDK releases we'll know which shape to commit to. | `transports/http_server.py` inline comments |

## Section 2 — New tools & surfaces

| ID | Item | Target | Why deferred | References |
|---|---|---|---|---|
| DEF-010 | **Data Product tools** — `datasphere_data_product_list`, `_get`, `_describe`, lineage / freshness surfaces | 1.1 | SAP's officially endorsed agent surface (per the Sapphire 2026 + API Policy v4 framing). Designing the tool set well takes a deliberate research pass; shipping a half-baked version would burn the slot. ADR-009 chose to keep 1.0 surface narrow. | `ProjectPlan_v1.0.md §2.2`, `Decisions_v1.0.md ADR-009` |
| DEF-011 | SAP Knowledge Graph integration (SPARQL passthrough, graph+vector retrieval) | post-1.0 | Datasphere-side maturity is early; the SAP HANA Cloud surface lands first. Revisit Q3 2026 once the help.sap.com docs stabilize. | Research agent A report, "What's NEW worth adding" |
| DEF-012 | Lineage / data quality first-class tools (`datasphere_catalog_lineage`, `datasphere_catalog_data_quality`) | 1.1 | Partial coverage already exists via `datasphere_catalog_get_asset` raw payload. A dedicated surface needs SAP's lineage REST shape to settle (it changed twice in the last 12 months). | Research agent A report |
| DEF-013 | BDC Delta Sharing resolver — tool that resolves a Datasphere data product to its Delta Sharing endpoint | sibling repo | This is properly a BDC concern. The sibling [SAPBDCMCP](https://github.com/rahulsethi/SAPBDCMCP) repo will own it; we may add a thin pointer tool here in 1.1 if it makes cross-product workflows obviously better. | Research agent A report |
| DEF-014 | Joule-for-Datasphere passthrough | post-1.0 (unscheduled) | No public REST/MCP endpoint is documented as of May 2026; the integration is SAP-internal. Watch for an announcement at TechEd 2026. | Research agent A report |
| DEF-015 | Task Chain API write tools (`datasphere_tasks_run_chain`) | **never in 1.x** | Violates the read-only posture (`Decisions_v1.0.md ADR-010`). Out of scope permanently for the 1.x line; would require a separate companion server with a different security profile. | `Decisions_v1.0.md ADR-010` |
| DEF-016 | Database user CRUD (`create_database_user`, `reset_password`, etc.) | **never** | Same as above — this is the "Mario foot-gun" we deliberately don't ship (`Decisions_v1.0.md ADR-010`). Read-only positioning is a marketing asset. | `Decisions_v1.0.md ADR-010` |

## Section 3 — Distribution & operations

| ID | Item | Target | Why deferred | References |
|---|---|---|---|---|
| DEF-020 | PyPI upload of `sap-datasphere-mcp 1.0.0` | manual pre-release gate | Tag-triggered; token rotation pending. CI workflow builds the wheel but does not publish. | `ImplementationTracker_v1.0.md H4` |
| DEF-021 | npm publish of `@rahulsethi/sap-datasphere-mcp 1.0.0` | manual pre-release gate | Same as DEF-020. | `ImplementationTracker_v1.0.md H5` |
| DEF-022 | GitHub Release notes assembly + asset upload | manual pre-release gate | After PR lands and tag is cut. | `ImplementationTracker_v1.0.md H6` |
| DEF-023 | TestPyPI upload + scratch-venv install smoke | manual pre-release gate | Belt-and-suspenders verification before the real PyPI publish. | `ImplementationTracker_v1.0.md` Pre-release gates |
| DEF-024 | Sibling SAPBDCMCP — open the cross-link PR adding the reciprocal `## Family` section to its README | sibling repo, pre-release | Closes the family-cohesion loop. Targeted at SAPBDCMCP v0.3.0 cadence. | `Decisions_v1.0.md ADR-012`, `ImplementationTracker_v1.0.md K7` |
| DEF-025 | Sibling SAPBDCMCP — fix the unresolved `<<<<<<< HEAD` merge marker in its `pyproject.toml` on `main` | sibling repo | Flagged by the BDCMCP analysis agent. Not our PR to merge, but worth tracking. | Research agent C report |
| DEF-026 | Sibling SAPBDCMCP — align build backend from setuptools to hatchling for family consistency | sibling repo, post-1.0 | Family-consistency item that costs the sibling more than us; let it land on its own cadence. | `Decisions_v1.0.md ADR-008` notes |

## Section 4 — Documentation & ecosystem

| ID | Item | Target | Why deferred | References |
|---|---|---|---|---|
| DEF-030 | `docs/v1.0/TestPrompts_v1.0.md` | 1.0.x | Lift the v0.3 pattern; one human-QA prompt per category. Useful for the first batch of users; not blocking the release. | `ImplementationTracker_v1.0.md J5` |
| DEF-031 | Refresh `docs/Architecture.png` for 1.0 | 1.0.x | Existing image was generated for v0.3 layout. ASCII diagram in `Architecture_v1.0.md §1` carries the load for now. | `ImplementationTracker_v1.0.md J16` |
| DEF-032 | `docs/SAP_API_POLICY.md` (developer-facing mirror) | 1.0.x | `public_docs/SAP_API_POLICY.md` is the user-facing source. A developer-facing version with extra implementation notes might be useful; not blocking. | `ImplementationTracker_v1.0.md J15` |
| DEF-033 | Fill `<contact@your-org-here>` placeholder in `public_docs/COMMERCIAL_LICENSING.md` | manual pre-release gate | One-line edit before tag. The doc agent left it as a clearly-flagged placeholder so it can't ship by accident. | `public_docs/COMMERCIAL_LICENSING.md` §4 |
| DEF-034 | `ruff check` baseline pass (lint cleanups) | 1.0.x | CI gates `ruff check` so regressions are caught, but the first run will surface ~20-50 historical complaints from `tasks.py` that should be cleaned up incrementally. | `ImplementationTracker_v1.0.md I3` |
| DEF-035 | Apply to the Anthropic MCP registry | post-1.0 | Surface should stabilize for a few weeks first; the registry application asks for prior real-world usage anyway. | `ProjectPlan_v1.0.md §2.2`, `Decisions_v1.0.md ADR-009` |
| DEF-036 | Listing in `marianfoo/sap-ai-mcp-servers` (community SAP MCP catalog) | post-1.0 | Quick PR after tagging; helps discovery. | Research agent B report |

## Section 5 — Manual pre-release gates (operational)

These are not code changes — they're one-shot operations that the maintainer
must complete before publishing `v1.0.0`. Listed here so they don't get
lost between branches.

- [ ] Live-tenant smoke of all 5 MCP Prompts (`profile_dataset`, `audit_space`, `explain_analytical_model`, `compare_assets`, `find_data_about_topic`); save transcripts to release notes.
- [ ] MCP Inspector verification of all 4 MCP Resources (`datasphere://space/{id}` family).
- [ ] mTLS-bound client_credentials end-to-end against an IAS-configured tenant (proves `DATASPHERE_OAUTH_MTLS_CERT`/`_KEY` works).
- [ ] HTTP transport with `DATASPHERE_MCP_BEARER_TOKEN` set against the installed MCP SDK (proves the bearer-auth probe finds an attach point on 1.25+).
- [ ] Live tenant on `DATASPHERE_API_PATH_LEGACY=0` and `=1` to confirm both paths still resolve.
- [ ] `pip install sap-datasphere-mcp` from TestPyPI works in a scratch venv (3.11, 3.12, 3.13 each at least once).
- [ ] `npx -y @rahulsethi/sap-datasphere-mcp --wrapper-version` works on Linux + macOS + Windows.
- [ ] All CI matrix cells green on the release SHA.
- [ ] `<contact@your-org-here>` filled in (DEF-033).
- [ ] Sibling SAPBDCMCP `## Family` PR opened (DEF-024).
- [ ] Tag `v1.0.0` cut; GitHub Release published with built wheel + sdist attached.

---

## Things this list is NOT

- It is not a 1.1 roadmap. Items targeted at 1.1 here are *intent*, not *commitment*. The 1.1 planning pass will reconsider every line.
- It is not a refused-features bucket. Anything genuinely out of scope for the project (write tools, anything mutating tenant state, any non-public SAP API) is captured in `ProjectPlan_v1.0.md §2.2` and `Decisions_v1.0.md` ADR-010 — and is marked **never** here, not deferred.
- It is not a substitute for `docs/backlog.md`. Items in `backlog.md` are open-ended product ideas; this file is the disciplined deferral list for the v1.0 release specifically. Once 1.0 ships, items here either move into a versioned plan (1.0.x / 1.1) or are recycled into backlog ideas.

## How to mark something done

When an item lands in a subsequent release:

1. Delete the row here (don't strikethrough — it pollutes the file over time).
2. Add a `Done in: vX.Y.Z` line at the matching row in `ImplementationTracker_v<that-version>.md`.
3. Mention the closure in that release's `CHANGELOG.md` entry under the **Migration** or **Changed** subsection.

When an item is recategorized as "never" (won't ship in 1.x), move the row to
`ProjectPlan_v1.0.md §2.2 "Non-goals (explicitly)"` or an ADR addendum.
