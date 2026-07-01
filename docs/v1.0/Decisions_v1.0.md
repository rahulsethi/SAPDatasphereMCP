# SAP Datasphere MCP Server — v1.0 Architecture Decisions

> ⚠️ **As-shipped reconciliation — added 2026-07-01 (post-dates these ADRs).** Two decisions below were amended/reversed during execution (see the per-ADR notes on ADR-002 and ADR-006). Where this document disagrees with the shipped code / root `LICENSE` / `CHANGELOG.md`, **the code is authoritative**:
>
> - **License (ADR-002):** shipped under the **Business Source License 1.1 (BSL 1.1)**, converting to Apache 2.0 on 2029-01-01 — **not** PolyForm Noncommercial. Same noncommercial-free / commercial-paid intent.
> - **PyPI distribution name (ADR-006):** rename **reverted** — kept as **`mcp-sap-datasphere-server`** (the short name is an unrelated community package). A `mcp-sap-datasphere-server` console-script alias was added; install with **`uvx mcp-sap-datasphere-server`**.
> - **mTLS (Tier C):** documented posture only — the `DATASPHERE_OAUTH_MTLS_CERT`/`_KEY` binding is **not yet implemented** in `auth.py` (roadmap).
>
> ADRs are historical records and are preserved as-written; the notes reconcile them with what shipped.

This document records the discrete architectural and product decisions taken for
the v1.0 release. It complements `ProjectPlan_v1.0.md`, which describes the
release holistically; this file captures the rationale and rejected alternatives
that would otherwise be lost between releases.

Format: Michael Nygard ADR. Each ADR is independent and can be linked to in
isolation. Where an ADR cross-references plan content, it points at a section of
`ProjectPlan_v1.0.md` rather than restating it.

---

## ADR-001: Cut a 1.0 release rather than a 0.4

**Status:** Accepted

**Date:** 2026-05-30

**Context**

Three breaking changes converge in this release window: the SAP API path
migration from `/api/v1/dwc/*` to `/api/v1/datasphere/*` (see ADR-005), the PyPI
distribution rename from `mcp-sap-datasphere-server` to `sap-datasphere-mcp`
(see ADR-006), and a full tool-naming overhaul to `datasphere_<category>_<verb>`
(see ADR-003). A fourth breaking change — the MIT to PolyForm Noncommercial
relicense (see ADR-002) — is bundled in for family-alignment reasons.

The external context has also shifted materially since v0.3.0 shipped in
January 2026. SAP API Policy v4/2026 becomes effective on 9 June 2026. The
SAP and Anthropic Sapphire partnership has put first-party Claude tooling on
the SAP roadmap. The competing community project MarioDeFelipe/sap-datasphere-mcp
has reached v1.2.1 with 45 tools.

**Decision**

Ship this release as v1.0.0. The version number is the message: this is the
graduation moment for the server.

**Consequences**

- A single user-disruption event amortizes four breaking changes instead of
  spreading the pain across three minor releases.
- The release narrative — "v1.0, aligned with API Policy v4/2026, in the
  Sapphire-Claude era" — is internally coherent and externally legible.
- Procurement reviewers reading the version number get a credible signal of
  maturity; pre-1.0 framing would have undersold the governance work in ADR-004.
- Future minor releases (1.1, 1.2) inherit the contract stability promise that
  a 1.0 implies; we now owe a deprecation window for every public surface.

**Alternatives considered**

(a) **A 0.4 patch release** carrying only the API path migration. Safer to
land, but undersells the governance layer, the Prompts/Resources work
(ADR-009), and the family alignment. Leaves the rename and tool overhaul
hanging over a future release.

(b) **A phased 0.4 → 0.5 → 1.0 path over six months.** Spreads disruption
across three upgrade events; loses the cohesive narrative; lets the
competitor extend its lead during the staging window.

(c) **Skip to 2.0** to match Mario's v1.2 numbering. Strange optics for a
first-time release at this name; implies a 1.x that never existed.

---

## ADR-002: Relicense from MIT to PolyForm Noncommercial 1.0.0

> **Amended in execution (2026-07-01):** shipped under the **Business Source License 1.1 (BSL 1.1)**, *not* PolyForm Noncommercial. BSL 1.1 delivers the same noncommercial-free / commercial-paid split (via its Additional Use Grant) and additionally converts to Apache 2.0 on 2029-01-01. The MIT→noncommercial *intent* recorded below holds; only the specific license changed. Ground truth: root `LICENSE`.

**Status:** Accepted — *license choice amended in execution (see note above)*

**Date:** 2026-05-30

**Context**

The sibling repository SAPBDCMCP relicensed to PolyForm Noncommercial 1.0.0 at
its v0.2.0 release. The family-alignment commitment recorded in Section 11 of
`ProjectPlan_v1.0.md` requires the two repos to ship under the same license, or
the "family" framing is hollow. PolyForm Noncommercial preserves free use for
individuals, education, research, and open-source projects while reserving
commercial use for separate licensing — a deliberate moat that does not block
the community story.

**Decision**

Relicense the v1.0 codebase to PolyForm Noncommercial 1.0.0. Replace `LICENSE`
in the repo root and update `pyproject.toml`'s `license` field. v0.3.1 and all
earlier tags remain under MIT — PolyForm only governs new commits made on or
after the 1.0 cut and any distribution downloaded from 1.0 onward. Add a new
`COMMERCIAL_LICENSING.md` at the repo root describing a friendly, low-friction
path to obtain a commercial license, with contact details and turnaround
expectations.

**Consequences**

- The "SAP MCP family" framing in the README and public docs becomes truthful.
- Commercial deployments need a license conversation; this is the intended moat.
- Anyone running v0.3.1 retains MIT rights forever on that artifact — there is
  no retroactive relicensing.
- README badges and the PyPI classifier list change in lockstep with the file
  swap; any downstream packagers reading the license metadata will see the
  change at 1.0.0.

**Alternatives considered**

(a) **Pull the sibling back to MIT.** Easier community story, gives up the
commercial moat the sibling team has already committed to.

(b) **Apache-2.0 + a commercial addendum.** Better explicit patent grant than
PolyForm, but no built-in commercial gate; would require a separate CLA and
trademark regime to recreate the moat.

(c) **Document the divergence** — sibling on PolyForm, Datasphere on MIT.
Workable but visibly undercuts the family story we have committed to and
gives external observers an obvious thread to pull on.

---

## ADR-003: Adopt `datasphere_<category>_<verb>` tool naming

**Status:** Accepted

**Date:** 2026-05-30

**Context**

The sibling SAPBDCMCP uses category-prefixed tool names of the form
`bdc_<category>_<verb>`. v0.3 of this server uses flat `datasphere_<verb>`
names. With 22 tools in 1.0 and more planned, flat names are increasingly
unreadable in MCP client palettes — particularly the Claude Desktop and Cursor
tool pickers where tools sort alphabetically and visually cluster only by
prefix. See Section 6.1 of `ProjectPlan_v1.0.md` for the full old→new mapping.

**Decision**

Rename all 22 tools to category-prefixed names. The seven categories are
`connectivity`, `catalog`, `query`, `discover`, `profile`, `summarize`, and
`governance`. Register every old name as a deprecation alias that resolves to
the new implementation. On first invocation per process, an alias emits a
single structured log record at WARNING level with the old name, new name, and
the calling tool's category — exactly once, then stays silent for the rest of
the process lifetime. Aliases remain through 1.1 and are removed in 1.2.

**Consequences**

- MCP client palettes group related tools visually; a user scanning for query
  tools sees `datasphere_query_*` adjacent.
- The deprecation log is structured so downstream log scrapers can count alias
  use across a fleet; this informs the 1.2 removal go/no-go.
- The alias layer adds one indirection in `tools/__init__.py` registration; no
  runtime cost beyond the first-call log.
- Documentation, README examples, and the public docs must update in the same
  commit as the rename, or screenshots and copy-paste examples drift.

**Alternatives considered**

(a) **Aliases only, keep both names side-by-side forever.** Doubles tool count
in MCP clients; defeats the navigability win that motivated the rename.

(b) **Keep flat naming, align everything else with the sibling.** Defensible,
but misses the family-cohesion benefit a user gets from running both servers
side by side and seeing the same naming convention.

---

## ADR-004: Full port of governance modules from SAPBDCMCP

**Status:** Accepted

**Date:** 2026-05-30

**Context**

SAP API Policy v4/2026 (effective 9 June 2026) requires a credible governance
posture from any tool calling SAP APIs at meaningful volume. The sibling
SAPBDCMCP already ships an audit log, policy enforcement, output redaction,
and per-tool risk metadata — work that has been hardened through its own
release cycle. Rebuilding any of this from scratch would duplicate effort and
diverge the family. See Section 9 of `ProjectPlan_v1.0.md` for the full
governance layer design.

**Decision**

Port `audit.py`, `policy.py`, `policy_evidence.py`, `redaction.py`, plus
`tools/_gated.py` and `tools/_metadata.py` from the sibling at 1.0. Adapt
each to the read-only Datasphere context — most notably, redaction patterns
gain Datasphere-specific identifiers (space IDs, HRID patterns) and policy
defaults reflect the absence of write tools (ADR-010). Add two new tools that
are net-new to the family: `datasphere_governance_api_policy_check`, which
returns the deployment's posture and configured limits, and
`datasphere_governance_audit_tail`, which returns recent audit records
(gated behind a `DATASPHERE_GOVERNANCE_AUDIT_TAIL=1` env flag, off by default).

**Consequences**

- The "API Policy v4/2026 aligned" claim in the README is backed by code, not
  marketing copy.
- An audit record is written for every tool invocation; operators get a
  per-process append-only log they can ship to their SIEM.
- The two new governance tools count against the 22-tool catalog and are
  themselves audited — `audit_tail` redacts its own output when redaction is on.
- Sibling parity creates a backport pathway: bug fixes in either repo's
  governance layer port across with minimal friction.

**Alternatives considered**

(a) **Light port** — audit and per-tool risk metadata only, defer policy and
redaction to 1.1. Cheaper to ship; leaves a visible governance gap against
the sibling and against the API Policy date.

(b) **Docs-only disclosure** — describe a posture in `SECURITY.md`, ship no
enforcement. Cheapest possible option, undercuts the "aligned" framing, and
fails any procurement review that reads past the README.

---

## ADR-005: Default API path order flips to `/api/v1/datasphere/*`

**Status:** Accepted

**Date:** 2026-05-30

**Context**

SAP deprecated the `/api/v1/dwc/*` path prefix in Datasphere Wave 2025.19. The
official support window for the legacy prefix closes in March 2027. Today,
both prefixes resolve on most tenants, but tenants on newer SAP-managed
regions are already returning 404 on `/dwc` for some endpoints. v0.3 of this
server tries `/dwc` first in `_client.py`'s path-candidate list, which is now
the wrong default. See Section 10 of `ProjectPlan_v1.0.md` for the testing
plan against both path styles.

**Decision**

Invert the path-candidate ordering in `src/sap_datasphere_mcp/_client.py` —
every API helper tries `/api/v1/datasphere/...` first and falls back to
`/api/v1/dwc/...` on 404 or 405. Add a `DATASPHERE_API_PATH_LEGACY=1`
environment variable that, when set to a truthy value, restores the legacy-first
order for tenants where the new prefix is broken or slower. Document the env
override prominently in `README.md` and the public docs, and surface it in the
output of `datasphere_governance_api_policy_check` so an operator can see
which order is active.

**Consequences**

- Tenants on current SAP regions stop paying a wasted-request penalty on every
  call — the 404 on `/dwc` was cheap but real, and showed up in latency p95s.
- Tenants still pinned to old regions can opt in to legacy-first with one env
  var and zero code change.
- The 404/405 fallback path remains hot until the March 2027 support window
  closes; we remove the fallback entirely in the release that follows that
  date (likely 1.4 or 2.0).
- Telemetry tip: log a counter when the fallback fires; if it stays at zero
  across a release cycle, we have evidence to remove it earlier.

**Alternatives considered**

(a) **Hard cutover to `/datasphere` only.** Breaks every tenant stuck on a
region SAP has not yet migrated; we have no way to know who those tenants
are. Unacceptable for a 1.0.

(b) **Leave the default order alone and document the env override.** Passively
misses the policy-date messaging and leaves modern tenants paying the
wasted-request tax.

---

## ADR-006: Rename the PyPI distribution to `sap-datasphere-mcp`

> **Reverted in execution (2026-07-01):** the rename did **not** ship. `sap-datasphere-mcp` is taken on PyPI by an unrelated community package, so the distribution **stayed `mcp-sap-datasphere-server`**. Instead, a `mcp-sap-datasphere-server` console-script alias was added so `uvx mcp-sap-datasphere-server` resolves the server. The `pip uninstall/install sap-datasphere-mcp` commands below are obsolete — upgrade in place with `pip install --upgrade mcp-sap-datasphere-server`.

**Status:** Reverted — *not shipped (see note above)*

**Date:** 2026-05-30

**Context**

The current PyPI distribution is `mcp-sap-datasphere-server`. It is verbose,
does not match the sibling's `sap-bdc-mcp`, and does not match this server's
own console script name `sap-datasphere-mcp`. New users routinely guess the
shorter name and end up on PyPI's "did you mean" page.

**Decision**

Rename the PyPI distribution to `sap-datasphere-mcp` at 1.0.0. Publish 1.0.0
under the new name; do not push 1.0.0 to the old distribution. Publish a
final 0.3.2 to the old distribution whose only behavioural change is a
DeprecationWarning at import time pointing at the new name and the migration
command. Existing v0.3.x users follow:

```
pip uninstall mcp-sap-datasphere-server
pip install sap-datasphere-mcp
```

The Python import path (`sap_datasphere_mcp`) does not change, so `from
sap_datasphere_mcp import ...` continues to work across the rename.

**Consequences**

- The distribution name, the console script name, the GitHub repo name, and
  the sibling's naming all align.
- PyPI search and `pip install` autocomplete favor the new name immediately.
- Anyone with `mcp-sap-datasphere-server` pinned in a requirements file gets
  the DeprecationWarning at import; CI logs will surface the migration to
  operators who don't read release notes.
- The old distribution name is held but unpublished after 0.3.2; this is a
  guard against name-squatting.

**Alternatives considered**

(a) **Keep the old name.** Verbose, divergent from the sibling, divergent from
our own console script. The cheapest option, but the friction compounds.

(b) **Publish a meta-package shim** under the old name that depends on the new
distribution. Adds a surface area we then have to deprecate in 1.2 or 2.0;
the pip uninstall/install path is acceptable for the v0.3.x population.

---

## ADR-007: Ship via PyPI, npx, and uvx

**Status:** Accepted

**Date:** 2026-05-30

**Context**

MarioDeFelipe's competing server ships on PyPI, npm, and uvx. The sibling
SAPBDCMCP ships on PyPI and npm (via an npx wrapper). v0.3 of this server
ships PyPI only. npm-native developers — particularly the Cursor and
Claude Desktop populations — typically reach for `npx` even for Python-backed
MCP servers, and the absence of an npm path leaves us off the default install
instructions in those clients' docs. See Section 12 of `ProjectPlan_v1.0.md`
for packaging detail.

**Decision**

Add an `npx-wrapper/` directory to the repo containing a minimal Node shim
package. The shim's `bin` entry runs `uvx sap-datasphere-mcp` with arguments
forwarded, matching the sibling pattern exactly. Publish the shim to npm as
`sap-datasphere-mcp` (same name as the PyPI distribution; npm and PyPI
namespaces do not collide). Document all three install paths — `pip`, `uvx`,
`npx` — side by side in `README.md` and the public docs.

**Consequences**

- npm-native developers get a one-line `npx sap-datasphere-mcp` invocation
  that matches what they expect from other MCP servers in their setup.
- The npm package is a thin shim — it has no Python code and no SAP code, so
  the surface area for npm-side CVEs is minimal.
- A new release now requires two publish steps (PyPI, then npm). The release
  checklist in Section 15 of `ProjectPlan_v1.0.md` lists these in order.
- `uvx` works directly off PyPI; we document it but it requires no separate
  artifact.

**Alternatives considered**

(a) **PyPI only.** Leaves npm-native developers on a worse path and undercuts
the sibling-parity story.

(b) **Native Node port.** Out of scope; duplicates the codebase; the value of
a native port for a thin SAP API wrapper is small.

---

## ADR-008: Bump Python floor to 3.11 and `mcp` SDK to `>=1.25.0`

**Status:** Accepted

**Date:** 2026-05-30

**Context**

The sibling SAPBDCMCP requires Python 3.11. The modern MCP SDK features this
release adopts — tool annotations (used in ADR-003 metadata), `outputSchema`
support (Section 6.3 of `ProjectPlan_v1.0.md`), and the structured-content
flow for Prompts (ADR-009) — require a recent SDK. v0.3 pins `mcp[cli]` at a
version that predates `outputSchema`, and `requires-python` is `>=3.10`.

**Decision**

Set `requires-python = ">=3.11"` in `pyproject.toml`. Pin
`mcp[cli]>=1.25.0` in the same file. Add `python-dotenv>=1.0.1` and
`jsonschema>=4.20.0` as direct dependencies (the former is consistent with
sibling, the latter validates `outputSchema` returns in tests). Update CI
matrices to test 3.11, 3.12, and 3.13.

**Consequences**

- Family alignment with SAPBDCMCP on interpreter floor — no chance of one
  repo working on a Python the other doesn't.
- The 3.10 user population (small but non-zero based on download stats) must
  upgrade. Release notes call this out as a breaking change; the version bump
  to 1.0 covers it.
- `outputSchema`, tool annotations, and Prompts ship cleanly without
  conditional imports or version-detection branches in our code.
- The transitive dep tree shrinks slightly (3.11+ stdlib subsumes some of
  what 3.10 needed via backports).

**Alternatives considered**

(a) **Stay on 3.10.** Loses sibling alignment and locks us out of MCP SDK
features the release is built around. We would either skip those features or
write feature-detection code that is itself a bug surface.

(b) **Bump to 3.12.** Too aggressive — enterprise SAP shops are still on 3.11
in many places and would not upgrade their interpreter to install an MCP
server. Hurts adoption with no benefit at this release.

---

## ADR-009: Ship MCP Prompts and Resources at 1.0

**Status:** Accepted

**Date:** 2026-05-30

**Context**

A survey of mature data-platform MCP servers (Snowflake, Databricks, Postgres
official, and the four largest community Postgres servers) finds that only
Databricks ships Prompts — eight of them. Zero servers in the SAP ecosystem
ship either Prompts or Resources. This is the cleanest field-first
differentiator available to us at 1.0, and the implementation cost is
contained because both surfaces are first-class in the `mcp` SDK we adopt in
ADR-008. See Sections 7 and 8 of `ProjectPlan_v1.0.md` for the schemas.

**Decision**

Ship five MCP Prompts at 1.0: `profile_dataset`, `audit_space`,
`explain_analytical_model`, `compare_assets`, and `find_data_about_topic`.
Each is templated, takes one or two arguments, and composes existing
tools — no new business logic enters the codebase through the Prompt layer.

Ship four MCP Resource URI patterns: `datasphere://space/{id}` and three
nested forms (`datasphere://space/{id}/asset/{asset_id}`,
`datasphere://space/{id}/connection/{name}`,
`datasphere://space/{id}/analytical_model/{name}`). Resource reads route
through the existing read-only tools and inherit their audit + redaction.

**Consequences**

- "First SAP MCP server with Prompts and Resources" is a true claim and goes
  on the README and the public docs.
- Prompts give the Claude Desktop "/" picker something to populate, which is
  a visible UX win the first time a user opens our server in that client.
- Resources let clients do citation-style attachment without first calling a
  tool — a real workflow win for the Claude desktop attachment flow.
- We owe stability on these URI shapes from 1.0 onward; renaming a Resource
  pattern in 1.1 would be a breaking change.

**Alternatives considered**

(a) **Skip — defer to 1.1.** Loses the differentiator at the release with the
most attention. No technical blocker, just scope discipline working against us.

(b) **Resources only, no Prompts.** Half-measure; gives up the desktop "/"
picker UX win.

(c) **Prompts only, no Resources.** Half-measure; gives up the attachment
flow and the URI-citation pattern Resources enable.

---

## ADR-010: Preserve strict read-only posture; reject database user CRUD

**Status:** Accepted

**Date:** 2026-05-30

**Context**

MarioDeFelipe's competing server ships `create_database_user`,
`update_database_user`, `delete_database_user`, and
`reset_database_user_password`. These tools target tenant admin surfaces — the
exact category of action that enterprise procurement reviewers flag as
unacceptable risk to delegate to an LLM. The competitor's tool count
advantage (45 vs our 22) is partly composed of tools we deliberately will
not ship.

**Decision**

Never ship write tools targeting tenant administrative surfaces. The 1.0
catalog is 100% read-only as enforced by `policy.py` (see ADR-004). The
read-only posture is a positioning asset: it appears in the README's first
paragraph, in `COMMERCIAL_LICENSING.md`, in the public docs, and in the
output of `datasphere_governance_api_policy_check` (ADR-004).

**Consequences**

- Procurement reviews that auto-reject any tool with a `create_*` or
  `delete_*` admin verb pass on first read.
- The "fewer tools but the right tools" framing differentiates the README
  introduction from a tool-count race.
- If a future release ever needs a controlled write surface (e.g., importing
  a CSN file), it ships under a dedicated category with explicit policy
  defaults that require operator opt-in; ADR-010 does not foreclose that, it
  forecloses the specific user-admin shape.
- Marketing copy commits us — backing off the read-only claim later would
  itself become news.

**Alternatives considered**

(a) **Add write tools behind a hard env flag, off by default.** Even with the
flag off, the tool exists in the codebase and shows up in code searches and
SBOMs. Procurement reviewers flag the import, not just the runtime path.

(b) **Match the competitor's surface.** Abandons positioning, invites the
foot-gun, makes the family-cohesion story (sibling is also read-first)
harder to tell.

---

## ADR-011: Facade refactor of `tools/`; defer deeper code split

**Status:** Accepted

**Date:** 2026-05-30

**Context**

`src/sap_datasphere_mcp/tools/tasks.py` is 1,931 lines and contains the 22
tool implementations as async functions. A clean structural split — moving
each category's implementations into its own module with proper imports,
shared helpers extracted, and tests rebalanced — is multi-day work and a
real regression risk against a release that already carries four other
breaking changes (ADR-001). See Section 5.1 of `ProjectPlan_v1.0.md` for
the target package layout.

**Decision**

At 1.0, ship per-category modules (`tools/connectivity.py`,
`tools/catalog.py`, `tools/query.py`, `tools/discover.py`, `tools/profile.py`,
`tools/summarize.py`, `tools/governance.py`) that re-export the existing
async functions from `tasks.py` and own only:

1. The new-name registration with the MCP server,
2. The per-tool annotations dict and the per-tool risk metadata,
3. The deprecation alias entries from ADR-003.

The actual async implementations stay in `tasks.py` unchanged. Defer the
logic-level decomposition (extracting shared helpers, splitting `tasks.py`
into category-aligned implementation files) to 1.1 or later.

**Consequences**

- External shape of the package — new module names, new tool names — matches
  the 1.0 design; downstream code that imports from `tools.connectivity`
  works as documented from day one.
- Internal shape is misleading: someone reading `tools/connectivity.py`
  expects to find implementations there and instead finds re-exports. Section
  5.1 of `ProjectPlan_v1.0.md` notes this; we should not hide it.
- Test surface stays addressed against `tasks.py`; no test churn at 1.0.
- 1.1 inherits a known-good refactor target.

**Alternatives considered**

(a) **Full split now.** Too much risk in the same release as the API path
flip, the rename, and the relicense. One of those failing the release-gate
checks is recoverable; the combination plus a logic refactor is not.

(b) **Single-file forever.** Misses the family-alignment win — sibling has
per-category modules, and side-by-side code reads should match.

---

## ADR-012: Cross-link the sibling READMEs

**Status:** Accepted

**Date:** 2026-05-30

**Context**

The two siblings — SAPDatasphereMCP (this repo) and SAPBDCMCP — do not
currently advertise each other from their READMEs. MarioDeFelipe ships
competing servers for both Datasphere and BDC; a unified family front is a
competitive necessity. See Section 11 of `ProjectPlan_v1.0.md` for the broader
family-alignment work.

**Decision**

Add a `## Family` section to both READMEs. Each section contains a one-paragraph
blurb naming the other repo, a reciprocal link, and a sentence describing what
shared design choices the family commits to (PolyForm license, `_<category>_<verb>`
naming, read-first posture, MCP SDK floor). Open the sibling PR alongside the
1.0 release of this repo so both READMEs ship the cross-link in the same week.

**Consequences**

- A reader landing on either repo via search discovers the other within a
  scroll.
- The family commits become visible and quotable — a procurement review of
  one repo can cite the other as a consistency point.
- A future divergence (one repo dropping PolyForm, one repo changing tool
  naming) becomes a README edit that we will notice, instead of a silent
  drift.
- Cost: one PR in each repo, kept tightly scoped to the README section.

**Alternatives considered**

(a) **Skip.** Cheapest option; undercuts the family-alignment story we have
committed to in ADR-002, ADR-003, ADR-004, ADR-008, and ADR-011. Hard to
justify having taken all those alignment costs and then declining the free
README win.
