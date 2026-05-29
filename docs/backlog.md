<!-- SAP Datasphere MCP Server -->
<!-- File: backlog.md -->
<!-- Version: v5 -->

# Backlog – SAP Datasphere MCP Server

This backlog merges:

- earlier backlog items (DevAssist, OLAP, transport, observability, safety, etc.),
- new ideas from v0.2/v0.3 planning (plugins, Data Products, RAG, governance),
- a **tier classification**:

- **Open-core** – stays in the public, MIT-licensed GitHub repo.
- **Premium / Enterprise plugins** – future commercial add-ons that plug into the open-core server.

Backlog items are *ideas*, not commitments. Targets are approximate.

---

## Legend

- **Status:**
  - Idea – rough idea, not fully designed
  - Planned – likely to be pulled into the next 1–2 releases
  - Parked – deliberately postponed / maybe never

- **Target:**
  - v0.3+ – candidate for the next minor release
  - Unsized – no target yet
  - Maybe – unsure if we ever want to do this

- **Tier:**
  - Open-core – public project
  - Premium – commercial plugin / extension

---

## 1. DevAssist / Sethi Integration (Future)

> Integration is **not** part of v0.3. It stays here as a future idea only; concrete scope and timing will be decided later.

| Item                                                      | Status  | Target | Tier      | Notes |
|-----------------------------------------------------------|---------|--------|-----------|-------|
| Define MCP server contract for DevAssist/Sethi integration | Idea   | Unsized| Open-core | Decide which tools are exposed, how they’re grouped, and how prompts reference them. To be revisited once DevAssist/Sethi is more mature. |
| Example wiring/config for DevAssist/Sethi + MCP server    | Idea    | Unsized| Open-core | Config snippets and high-level usage guidance; no commitment to a version yet. |
| Higher-level agents using Datasphere MCP tools via DevAssist/Sethi | Idea | Unsized| Premium | Agents that combine Datasphere with other systems (BW, HANA, logs) for enterprise workflows. |

---

## 2. Analytical / OLAP Capabilities

| Item                                                      | Status  | Target | Tier      | Notes |
|-----------------------------------------------------------|---------|--------|-----------|-------|
| Basic analytical query API for analytical models          | Planned | v0.3+  | Open-core | Minimal listing + constrained queries (measures, dimensions, simple filters). |
| Analytical model discovery & navigation tools             | Idea    | v0.3+  | Open-core | List analytical datasets, measures, dimensions; simple exploration. |
| Pre-built OLAP summaries / rollup helpers                 | Idea    | Unsized| Premium   | Convenience tools for common aggregates (e.g. time series, segment breakdowns). |
| Advanced OLAP analysis macros (trend/segment comparison)  | Idea    | Unsized| Premium   | High-level tools that orchestrate multiple analytical queries and return narrative + structured output. |

---

## 3. Transport & Deployment

| Item                                                      | Status  | Target | Tier      | Notes |
|-----------------------------------------------------------|---------|--------|-----------|-------|
| HTTP transport for MCP server (in addition to stdio)      | Idea    | v0.3+  | Open-core | Run as long-lived service; minimal, secure-by-default HTTP interface. |
| Docker image for MCP server                               | Idea    | v0.3+  | Open-core | Basic Dockerfile/image published with releases; good for local + simple server use. |
| Kubernetes deployment template (simple)                   | Idea    | Unsized| Open-core | Lightweight example manifest/Helm chart for dev/test clusters. |
| Opinionated enterprise K8s deployment (monitoring, RBAC)  | Idea    | Unsized| Premium   | Hardened K8s package with logging, metrics, secrets, and RBAC tuned for enterprises. |

---

## 4. Observability & Operations

| Item                                                      | Status  | Target | Tier      | Notes |
|-----------------------------------------------------------|---------|--------|-----------|-------|
| Structured JSON logging with log-level control            | Planned | v0.3+  | Open-core | v0.3 introduces base; long-term aim is consistent JSON logs with correlation IDs. |
| Metrics/telemetry integration (e.g. Prometheus-friendly)  | Idea    | v0.3+  | Premium   | Track request counts, latency, error breakdowns per tool for production-grade monitoring. |
| Centralised configuration of rate limits per tool         | Idea    | Unsized| Premium   | Prevent agents from hammering heavy tools; more configurable than basic row caps. |

---

## 5. Advanced Data Intelligence (joins, semantics, trends)

| Item                                                      | Status  | Target | Tier      | Notes |
|-----------------------------------------------------------|---------|--------|-----------|-------|
| Automatic join-path suggestion across assets              | Idea    | v0.3+  | Premium   | Use keys & stats to propose likely joins; high-value for LLMs. |
| Space-level semantic summaries                            | Idea    | v0.3+  | Open-core | Natural-language summaries of a space using existing metadata/profiles. v0.3 adds first summaries. |
| Time-series / trend detection helpers                     | Idea    | Maybe  | Premium   | Tools that detect obvious trends/seasonality in numeric time-series. |
| Cross-asset “relationship map” viewer                     | Idea    | Unsized| Premium   | Graph-like view of how assets relate (joins, dependencies). |

---

## 6. Safety & Access Patterns

| Item                                                      | Status  | Target | Tier      | Notes |
|-----------------------------------------------------------|---------|--------|-----------|-------|
| Configurable row/size limits per tool                     | Planned | v0.3+  | Open-core | Part of v0.3 hardening; env-based caps per tool type. |
| Simple rate-limiting (per tool or per client)             | Idea    | Unsized| Premium   | Avoid abuse when plugged into many agents; more advanced than basic caps. |
| Optional “admin/ETL profile” with heavier tools           | Parked  | Maybe  | Premium   | Larger extracts, admin helpers; currently out-of-scope to keep server safe by default. |

---

## 7. Data Products, Data Mesh & Governance

| Item                                                      | Status  | Target | Tier      | Notes |
|-----------------------------------------------------------|---------|--------|-----------|-------|
| Basic Data Product explorer (list products)               | Idea    | v0.3+  | Open-core | Simple list: id, name, description, space/domain, owner if exposed. |
| Data Product overview summariser                          | Idea    | v0.3+  | Open-core | Lightweight summary per product: what it is, who owns it, which domain. |
| Data Product schema & lineage mapping                     | Idea    | Unsized| Premium   | Map products to underlying assets; expose lineage graph in JSON. |
| Domain / data mesh views                                  | Idea    | Unsized| Premium   | Views by domain, SLA, ownership; cross-domain product matrices. |
| Governance scorecards                                     | Idea    | Unsized| Premium   | Dashboards for documentation completeness, staleness, policy checks. |

---

## 8. RAG, Unstructured Data & Vector Features

| Item                                                      | Status  | Target | Tier      | Notes |
|-----------------------------------------------------------|---------|--------|-----------|-------|
| Semantic search / vector retrieval plugin                 | Idea    | v0.3+  | Premium   | RAG-style tools that use embeddings & HANA Cloud vector capabilities. |
| Hybrid structured + vector search                         | Idea    | Unsized| Premium   | Combine structured filters (space, asset) with semantic similarity. |
| Document-store bridges (HANA, external)                   | Idea    | Unsized| Premium   | Turn documents/JSON into RAG chunks and expose via MCP tools. |

---

## 9. LLM Ergonomics & Summarisation

| Item                                                      | Status  | Target | Tier      | Notes |
|-----------------------------------------------------------|---------|--------|-----------|-------|
| Asset/space/column summary tools (basic)                  | Planned | v0.3+  | Open-core | Wrap existing metadata/profiles into concise English summaries. |
| Narrative analysis macros (multi-step)                    | Idea    | Unsized| Premium   | “Analyze this domain”, “Explain last quarter’s trend” tools built atop multiple calls. |
| Prompt templates and multi-tool recipes                   | Idea    | v0.3+  | Premium   | Opinionated patterns for how LLM agents should orchestrate tools for advanced analysis. |

---

## 10. Transports, Plugins & Architecture

| Item                                                      | Status  | Target | Tier      | Notes |
|-----------------------------------------------------------|---------|--------|-----------|-------|
| Plugin registry & loading (`register_plugins(server)`)    | Planned | v0.3   | Open-core | Introduced in v0.3; core of the plugin architecture. |
| Stable plugin API guidelines                              | Planned | v0.3+  | Open-core | Document expectations for plugin modules (naming, registration, safety). |
| Premium plugin bundles (analytics, RAG, governance)       | Idea    | Unsized| Premium   | Separate packages depending on open-core library and using plugin hooks. |

---

## 11. Potentially Out-of-Scope (Documented)

These are things we *could* do technically but are intentionally **not part** of the near-term vision.

| Item                                                      | Status  | Target | Tier      | Notes |
|-----------------------------------------------------------|---------|--------|-----------|-------|
| Database user management tools (create/update/delete)     | Parked  | Maybe  | Premium   | High-risk; conflicts with read-only positioning of open-core. |
| Direct ETL/export tools for very large row counts         | Parked  | Maybe  | Premium   | Better handled by dedicated ETL tooling; MCP server stays focused on exploration & analytics. |

---

## 12. Strategy Notes (internal)

- **Open-core** remains the foundation:
  - transports (stdio, basic HTTP),
  - core tools (spaces, assets, metadata, profiling, basic analytical, summaries),
  - plugin registry and configuration,
  - Dockerfile and simple K8s templates.

- **Premium / enterprise plugins**:
  - live in separate repos/packages,
  - depend on open-core (`mcp-sap-datasphere-server`) as a library,
  - register their tools via the plugin registry,
  - focus on heavy-lift features:
    - advanced OLAP, RAG, macros,
    - governance dashboards,
    - enterprise deployment bundles (K8s + observability + security).
