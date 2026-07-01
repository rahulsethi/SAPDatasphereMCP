<!-- SAP Datasphere MCP Server -->
<!-- File: docs/v1.0/Architecture_v1.0.md -->
<!-- Version: v1.0 -->
<!-- Status: design / awaiting review -->
<!-- Author: Rahul Sethi -->
<!-- Date: 2026-05-30 -->

# SAP Datasphere MCP Server — v1.0 Architecture

> ⚠️ **As-shipped reconciliation — added 2026-07-01 (post-dates this design doc).** Several v1.0 decisions changed during execution. Where this document disagrees with the shipped code / root `LICENSE` / `CHANGELOG.md`, **the code is authoritative**:
>
> - **License:** shipped under the **Business Source License 1.1 (BSL 1.1)**, which converts to Apache 2.0 on 2029-01-01 — **not** PolyForm Noncommercial. The noncommercial-free / commercial-paid *intent* is unchanged.
> - **PyPI distribution name:** kept as **`mcp-sap-datasphere-server`** — the planned rename to `sap-datasphere-mcp` was reverted (that short name is an unrelated community package). A `mcp-sap-datasphere-server` console-script alias was added, so install with **`uvx mcp-sap-datasphere-server`** / **`pip install mcp-sap-datasphere-server`**. Any `pip install`/`uvx`/`pipx sap-datasphere-mcp` command below is obsolete — `sap-datasphere-mcp` is only the console-script/command name.
> - **mTLS (Tier C):** documented posture only — `DATASPHERE_OAUTH_MTLS_CERT`/`_KEY` are **not yet wired into the OAuth token flow** in `auth.py` (roadmap, not implemented).
>
> Corrected as-shipped docs live in root `CHANGELOG.md`, `LICENSE`, and `public_docs/`.

This document describes **how** the v1.0 server is put together. For **what** the
release contains and **why** the design choices were made, see the companion
[`ProjectPlan_v1.0.md`](./ProjectPlan_v1.0.md). Where the project plan answers
"24 tools across seven categories, ported from v0.3.1, plus governance," this
document answers "what does the wire path look like from `sap-datasphere-mcp`
through the tool decorator down to the SAP REST endpoint, and how do the audit
and policy hooks sit in the middle."

The v0.3 architecture note (`docs/Architecture.md`) is preserved for historical
reference. This file supersedes it for the 1.x line.

---

## 1. Layered view

The 1.0 server is organised as five horizontal layers, with three vertical
"interceptor" concerns (policy, audit, redaction) wrapping the tool boundary.

```text
+----------------------------------------------------------------------+
|                         MCP Host                                     |
|       Claude Desktop  /  Cursor  /  LibreChat  /  Inspector          |
+----------------------------------------------------------------------+
                              |   JSON-RPC over stdio
                              |   (or HTTP + optional bearer auth)
                              v
+----------------------------------------------------------------------+
|                       Transport layer                                |
|       transports/stdio_server.py  |  transports/http_server.py       |
+----------------------------------------------------------------------+
                              |   delegates to a shared factory
                              v
+----------------------------------------------------------------------+
|                  server.create_server()  (FastMCP)                   |
|   - constructs the FastMCP instance                                  |
|   - wires policy / audit / redaction interceptors                    |
|   - holds the DatasphereClient instance                              |
+----------------------------------------------------------------------+
       |                       |                         |
       v                       v                         v
+----------------+   +--------------------+   +-----------------------+
| tools.registry |   | prompts.register() |   | resources.register()  |
| register_all() |   |  5 MCP prompts     |   |  4 URI patterns       |
+--------+-------+   +--------------------+   +-----------------------+
         |
         v
+----------------------------------------------------------------------+
|                  Tool category facades                               |
|  connectivity / catalog / query / discover / profile /               |
|  summarize / governance   (re-export from tasks.py)                  |
+----------------------------------------------------------------------+
                              |
                              v
+----------------------------------------------------------------------+
|       Governance interceptor chain  (decorator stack)                |
|   policy.permits  ->  audit.start  ->  TOOL  ->  redaction.scrub     |
|                                                  ->  audit.commit    |
+----------------------------------------------------------------------+
                              |
                              v
+----------------------------------------------------------------------+
|                  tools/tasks.py — async impls                        |
|        (22 v0.3 functions; logic untouched in 1.0)                   |
+----------------------------------------------------------------------+
                              |
                              v
+----------------------------------------------------------------------+
|                  DatasphereClient (httpx)                            |
|   - _catalog_base_candidates  (modern -> legacy)                     |
|   - _consumption_base_candidates                                     |
|   - 404-driven fallback for path migration                           |
+----------------------------------------------------------------------+
       |                                                |
       v                                                v
+----------------+                              +--------------------+
| auth.OAuthClient|                             | cache.TTLCache     |
| client_creds + |                              | (metadata only)    |
| optional mTLS  |                              +--------------------+
+----------------+
       |
       v
+----------------------------------------------------------------------+
|                  SAP Datasphere REST                                 |
|   /api/v1/datasphere/consumption/catalog/*    (modern)               |
|   /api/v1/datasphere/consumption/relational/* (modern)               |
|   /api/v1/datasphere/consumption/analytical/* (modern)               |
|   /api/v1/dwc/...                             (legacy fallback)      |
+----------------------------------------------------------------------+
```

The plugin registry is a sibling of `tools.registry`: it runs after core tool
registration and is allowed to add tools but never to replace them.

---

## 2. Boot path and lifecycle

The console script `sap-datasphere-mcp` is the only entry point most users
will see. Its call sequence:

```text
1.  console script  sap-datasphere-mcp           (defined in pyproject.toml)
2.    transports.stdio_server:main()
3.      config = DatasphereConfig.from_env()     # reads ~25 env vars
4.      audit  = audit.open(config)              # opens JSONL handle if enabled
5.      policy = policy.from_config(config)      # picks strict vs. permissive
6.      mcp    = server.create_server(           # FastMCP instance
                    config=config,
                    audit=audit,
                    policy=policy,
                 )
7.        tools.registry.register_all(mcp, ...)  # 24 tools + 22 aliases
8.        prompts.register(mcp)                  # 5 prompts
9.        resources.register(mcp)                # 4 URI patterns
10.       plugins.registry.register_plugins(mcp) # zero or more external
11.     mcp.run(transport="stdio")               # event loop starts
```

Side-effect ordering matters and is fixed:

1. **Config load** comes first; nothing else can read `os.environ` directly.
2. **Audit handle open** is next so any registration failure is recorded.
3. **Policy mode determination** happens before tool registration so the
   `@gated` decorator can refuse to bind gated tools under strict mode.
4. **Core tool registration** then runs; failures here are fatal.
5. **Prompts and Resources** register; failures here are fatal (they ship in
   the package).
6. **Plugin discovery** runs last and failures are non-fatal — a broken
   third-party plugin must never prevent the core server from starting. The
   failure is captured in `datasphere_connectivity_plugins_status`.

The `python -m sap_datasphere_mcp` invocation (via the new `__main__.py`) is
an alternative entry point that calls the same `transports.stdio_server:main`.

The HTTP transport (`transports/http_server.py`) replaces step 11 with
`mcp.run(transport="streamable-http")` and wraps it in an ASGI app that adds:

- `GET /health` — returns `{ok, version, path_mode, policy_strict}`.
- Optional bearer-token check (`DATASPHERE_MCP_BEARER_TOKEN`); 401 if absent
  or wrong.

Everything from step 1 to step 10 is identical between the two transports.
That is the entire reason `server.create_server()` exists as a separate
module — to keep both wire mechanisms feeding the same MCP instance.

---

## 3. The facade pattern in `tools/`

This is the deliberate compromise at the heart of the 1.0 code organisation.

The v0.3 server kept all 22 tool implementations in a single 1,931-line
`tools/tasks.py`. The v1.0 plan wants:

- per-category modules so users (and IDE outlines) can find tools by area,
- new tool names (`datasphere_<category>_<verb>`) with deprecation aliases,
- per-tool risk metadata and `@gated` annotations,
- two new governance tools,

without rewriting business logic that the test suite already covers. A full
extraction (one file per tool, separate `core.py` for shared helpers, etc.)
is the right shape long-term but is **not** what 1.0 ships.

The compromise is a facade:

- `tools/tasks.py` is **kept verbatim** and holds the 22 async implementations.
- `tools/connectivity.py`, `tools/catalog.py`, `tools/query.py`,
  `tools/discover.py`, `tools/profile.py`, `tools/summarize.py` each
  **import** the relevant async functions from `tasks.py`, attach new names,
  attach per-tool metadata, and wrap them in MCP `@tool(...)` decorators.
- `tools/governance.py` adds the only genuinely new code paths
  (`api_policy_check`, `audit_tail`).
- `tools/_aliases.py` registers every old name as a one-line wrapper that
  calls the new tool and emits a deprecation log line.
- `tools/_gated.py` and `tools/_metadata.py` provide the decorators consumed
  by the category modules.
- `tools/registry.py` exports a single `register_all(mcp)` function that the
  server factory calls; it imports the seven category modules in a fixed
  order and lets each one register its tools.

```python
# tools/catalog.py  (illustrative, not the full file)
from .tasks import _list_spaces_impl       # original v0.3 async function
from ._metadata import tool_metadata
from ._gated   import gated
from ..schemas import list_spaces_schema

@tool_metadata(
    category="catalog",
    risk_level="low",
    data_class="metadata",
    policy_class="permitted_under_cc",
    output_schema=list_spaces_schema,
    aliases=["datasphere_list_spaces"],
)
@gated
async def datasphere_catalog_list_spaces(cursor: str | None = None):
    return await _list_spaces_impl(cursor=cursor)
```

The tradeoff is explicit and called out in the project plan: **rename,
governance, and annotations land in 1.0; deeper per-tool extraction is
deferred to 1.1+.** The cost is one extra import per tool. The benefit is
that the diff a code reviewer has to read for 1.0 stays scoped to the things
1.0 is actually changing.

---

## 4. Governance interceptor chain

Every tool call passes through a three-stage chain, implemented as a small
stack of decorators rather than a heavyweight middleware framework. The chain
is the same for every tool because it is applied by `tools.registry` at
registration time.

```text
inbound MCP request
   |
   v
+---------------------------+
| @gated                    |  policy.permits(tool_name, args)
| (tools/_gated.py)         |  -> False => return structured-error 'policy_denied'
+-------------+-------------+
              | True
              v
+---------------------------+
| audit.start_record()      |  open record { tool, args_fingerprint, ts_start }
+-------------+-------------+
              |
              v
+---------------------------+
| original async impl       |  (from tasks.py)
| - DatasphereClient call   |
| - shape result            |
+-------------+-------------+
              |
              v
+---------------------------+
| redaction.scrub(result)   |  apply regex patterns unless tool opts out
+-------------+-------------+
              |
              v
+---------------------------+
| audit.commit_record()     |  finalise { duration_ms, outcome, rows_returned }
+-------------+-------------+
              |
              v
JSON-serialisable dict back to MCP
```

A few intentional properties of this chain:

- **Decorator stack, not middleware framework.** Each layer is a normal Python
  async wrapper. There is no plugin system inside the chain, no router, no
  dynamic dispatch. The order is hard-coded in `_gated.py` / `_metadata.py`
  and the registry. We trade flexibility for legibility.
- **The audit record is opened before the tool runs.** This means failures,
  exceptions, and timeouts are auditable — the `commit_record` finaliser is
  in a `finally` block.
- **Redaction runs after the tool, before serialisation.** Per-tool opt-out
  is declared in `_metadata.py` for the handful of tools that need to surface
  redaction-recognisable URLs (e.g. `tenant_info`).
- **No I/O in `policy.permits`.** Policy evaluation reads in-memory tables
  from `policy_evidence.py` and the current strict-mode flag. It is sub-
  millisecond and never blocks.
- **Argument values are never logged.** The audit record carries a SHA-256
  fingerprint of the canonical arg JSON. This is also what enables
  `datasphere_governance_audit_tail` to be safe by default — it can never
  exfiltrate raw OAuth-bound query parameters.

The complete record shape is documented in `ProjectPlan_v1.0.md` section 9.1.

---

## 5. MCP Prompts and Resources

These are the two MCP-spec surfaces that no SAP MCP server has shipped yet.
Both are first-class packages in `src/sap_datasphere_mcp/`.

### 5.1 Prompts

Each of the five prompt modules under `prompts/` exports a single `PROMPT`
constant and a `render(args)` function:

```python
# prompts/profile_dataset.py
from mcp.types import Prompt, PromptArgument, PromptMessage

PROMPT = Prompt(
    name="profile_dataset",
    description="End-to-end profile of one Datasphere asset: schema, "
                "sample rows, per-column profile, deterministic summary.",
    arguments=[
        PromptArgument(name="space_id",   description="...", required=True),
        PromptArgument(name="asset_name", description="...", required=True),
    ],
)

def render(args: dict) -> list[PromptMessage]:
    return [
        PromptMessage(role="user", content=...),
        # assistant turn that calls catalog_get_asset, profile_schema,
        # query_preview, profile_column, summarize_asset in sequence
    ]
```

`prompts/__init__.py` exposes `register(mcp)` which:

1. Imports every sibling module.
2. For each, registers `module.PROMPT` and binds `prompts/get` to call
   `module.render(args)`.
3. The list returned by `prompts/list` is built from the registered set.

Prompts are deliberately **assembled message sequences that call tools**.
They are not free-form templates. This keeps the surface deterministic and
ensures prompts cannot bypass policy or audit — the tools they call go
through the normal chain.

### 5.2 Resources

`resources/catalog_resources.py` defines URI patterns and resolver functions:

```python
RESOURCE_PATTERNS = [
    ("datasphere://space/{space_id}",                          resolve_space),
    ("datasphere://space/{space_id}/asset/{asset_name}",       resolve_asset),
    ("datasphere://space/{space_id}/asset/{asset_name}/schema",resolve_schema),
    ("datasphere://space/{space_id}/asset/{asset_name}/sample",resolve_sample),
]
```

`resources/__init__.py` exports `register(mcp)`. For each pattern it:

1. Registers a URI matcher with the MCP runtime so `resources/list` can
   enumerate space-level URIs and assets exposed within them.
2. Binds the resolver to `resources/read`. Each resolver is a thin call into
   `DatasphereClient` followed by the same redaction step the tool chain
   uses — Resources are not allowed to leak data that tools would scrub.

The `/sample` resolver is strictly capped at `DATASPHERE_RESOURCE_SAMPLE_ROWS`
(default 5). The `/schema` resolver prefers `$metadata` (EDMX) and falls back
to a sample-derived schema only when `$metadata` is unavailable for that
asset class.

Tool responses that list assets (e.g. `datasphere_catalog_list_assets`) embed
the corresponding Resource URI alongside each entry so a host can pre-load
it without an extra tool call.

---

## 6. API path migration mechanics

The v0.3.1 client targeted `/api/v1/dwc/*` exclusively. The 1.0 client
targets `/api/v1/datasphere/*` by default and falls back to `/api/v1/dwc/*`
on a 404 from the new path. This is implemented as two ordered candidate
lists on `DatasphereClient`:

```python
class DatasphereClient:
    _catalog_base_candidates = (
        "/api/v1/datasphere/consumption/catalog",   # modern (try first)
        "/api/v1/dwc/catalog",                      # legacy fallback
    )
    _consumption_base_candidates = (
        "/api/v1/datasphere/consumption",           # modern
        "/api/v1/dwc/consumption",                  # legacy
    )
```

The request helper walks the candidates in order. On `404 Not Found` from
the first candidate, it transparently retries on the second and **records
which one succeeded** on a per-client-instance cache. Subsequent calls for
the same endpoint shape skip the lookup. Non-404 errors (401, 403, 5xx) are
**not** subject to fallback — they surface as structured errors immediately.

The mode is observable:

- `DatasphereClient.path_mode` returns `"modern"`, `"legacy"`, or `"mixed"`
  depending on what the cache has resolved.
- `datasphere_connectivity_diagnostics` surfaces `path_mode`.
- `datasphere_governance_api_policy_check` surfaces it alongside the policy
  posture.

For tenants on older waves where the modern paths are simply absent and
every probe wastes a round trip, `DATASPHERE_API_PATH_LEGACY=1` inverts the
order so the legacy paths are tried first. This is documented as an escape
hatch for stuck tenants and is expected to be removed when SAP retires the
`dwc` tree (March 2027). A "consider unsetting this" log line is emitted
when the modern path is found to work despite the legacy flag being set.

A `respx`-driven test in `tests/test_path_migration.py` exercises every
endpoint in both modes against fixture cassettes, so the migration is
covered without a live tenant.

---

## 7. Configuration model

All configuration is read by `config.py` into a single immutable
`DatasphereConfig` dataclass at boot. Nothing else in the codebase calls
`os.environ` directly.

| Env var | Default | Purpose |
|---|---|---|
| `DATASPHERE_TENANT_URL` | *(required)* | Base URL of the Datasphere tenant. |
| `DATASPHERE_OAUTH_TOKEN_URL` | *(required)* | OAuth2 token endpoint (IAS / XSUAA). |
| `DATASPHERE_CLIENT_ID` | *(required)* | OAuth2 client_id (technical user). |
| `DATASPHERE_CLIENT_SECRET` | *(required unless mTLS)* | OAuth2 client_secret. |
| `DATASPHERE_VERIFY_TLS` | `1` | TLS verification toggle. `0` disables (debug only). |
| `DATASPHERE_MOCK_MODE` | `0` | In-memory mock tenant; no network calls. |
| `DATASPHERE_PLUGINS` | *(empty)* | Comma-list of plugin specs (see plugin section). |
| `DATASPHERE_PLUGIN_TRUST` | *(empty)* | Allow-list for subprocess plugin upstreams. |
| `DATASPHERE_AUDIT_ENABLED` | `0` | Enable JSONL audit log. |
| `DATASPHERE_AUDIT_LOG_PATH` | `~/.cache/sap-datasphere-mcp/audit.log` | Audit file location. |
| `DATASPHERE_API_POLICY_STRICT` | `0` | Refuse gated tools; advisory in 1.0 (no gated tools ship). |
| `DATASPHERE_API_PATH_LEGACY` | `0` | Try `/api/v1/dwc/*` before `/api/v1/datasphere/*`. |
| `DATASPHERE_REDACTION_ENABLED` | `1` | Apply regex-based secret/PII scrubbing on tool returns. |
| `DATASPHERE_OAUTH_MTLS_CERT` | *(unset)* | Path to client cert PEM for RFC 8705 mTLS. |
| `DATASPHERE_OAUTH_MTLS_KEY` | *(unset)* | Path to client key PEM. |
| `DATASPHERE_MCP_TRANSPORT` | `stdio` | `stdio` or `http`. |
| `DATASPHERE_MCP_HOST` | `127.0.0.1` | HTTP bind host (HTTP transport only). |
| `DATASPHERE_MCP_PORT` | `8765` | HTTP bind port (HTTP transport only). |
| `DATASPHERE_MCP_BEARER_TOKEN` | *(unset)* | If set, HTTP transport requires this bearer header. |
| `DATASPHERE_RESOURCE_SAMPLE_ROWS` | `5` | Cap for the `/sample` Resource resolver. |
| `DATASPHERE_PREVIEW_MAX_ROWS` | `50` | Cap for `datasphere_query_preview`. |
| `DATASPHERE_QUERY_MAX_ROWS` | `1000` | Cap for `datasphere_query_relational` / `_analytical`. |
| `DATASPHERE_SEARCH_MAX_RESULTS` | `100` | Cap for `datasphere_discover_assets`. |
| `DATASPHERE_CACHE_TTL_SECONDS` | `300` | TTL for `cache.TTLCache` (metadata only). |
| `DATASPHERE_CACHE_MAX_ENTRIES` | `1024` | Cache capacity. |

Three properties of the config model worth noting:

1. **Immutable after load.** The dataclass is `frozen=True`. Reloading
   requires a server restart. This is deliberate — config drift across a
   long-running process is a real source of confusion in MCP servers.
2. **Defaults are conservative.** Caps are tight, audit is off, redaction is
   on. Operators opt into wider surfaces; we never default to "loud."
3. **mTLS is opt-in.** If both `DATASPHERE_OAUTH_MTLS_CERT` and
   `DATASPHERE_OAUTH_MTLS_KEY` are set, the OAuth client uses them and
   `DATASPHERE_CLIENT_SECRET` becomes optional.

---

## 8. Error and response shape

Every tool returns a JSON-serialisable dict. There are exactly two top-level
shapes — success and structured error — and every tool returns one of them.

**Success:**

```json
{
  "ok": true,
  "data": { /* tool-specific; validated against the tool's outputSchema */ },
  "meta": {
    "tool": "datasphere_query_relational",
    "duration_ms": 412,
    "rows_returned": 47,
    "cap_applied": false,
    "path_mode": "modern"
  }
}
```

**Structured error:**

```json
{
  "ok": false,
  "error": {
    "code": "policy_denied",
    "message": "Tool refused under DATASPHERE_API_POLICY_STRICT=1.",
    "hint": "Set DATASPHERE_API_POLICY_STRICT=0, or deploy via Integration Suite MCP Gateway."
  },
  "meta": {
    "tool": "datasphere_query_relational",
    "duration_ms": 1,
    "path_mode": "modern"
  }
}
```

Standard error `code` values:

| code | When |
|---|---|
| `policy_denied` | `@gated` refused the call. |
| `auth_failed` | OAuth token endpoint rejected the client credentials. |
| `not_found` | Both modern and legacy paths returned 404 for a resource. |
| `upstream_error` | Datasphere returned 5xx; details in `message`. |
| `invalid_argument` | Pydantic validation of the tool args failed. |
| `cap_exceeded` | Caller passed `top` greater than the configured cap **and** strict cap mode is on (1.0 default: clamp, do not error). |
| `mock_unavailable` | Tool not supported under `DATASPHERE_MOCK_MODE=1`. |

The `hint` field is mandatory on every error. The MCP host renders it
directly to the user, so it is written as a short imperative sentence with
the corrective action.

Pydantic argument validation happens **before** the `@gated` decorator runs,
so an `invalid_argument` error is never reflected in the audit log as a
denied call.

---

## 9. Plugin system

Plugins extend the tool surface without touching the core package. The
registry (`plugins/registry.py`) supports three plugin spec shapes, in
order of complexity:

| Spec | Form | Loading |
|---|---|---|
| Python module | `my_org.my_plugin` | `importlib.import_module(...)`; module must expose `register_tools(mcp)`. |
| `npx:` upstream | `npx:@vendor/some-mcp-server` | Spawned as a subprocess; its stdio MCP surface is proxied as namespaced tools. |
| `uvx:` upstream | `uvx:some-pypi-package` | Same as `npx:`, via `uv tool run`. |
| `cmd:` upstream | `cmd:/abs/path/to/binary --flag` | Same as `npx:`, with a literal command. |

The registry reads `DATASPHERE_PLUGINS` (comma-separated specs) and, for any
subprocess spec, refuses to spawn unless the spec is present in
`DATASPHERE_PLUGIN_TRUST` (also a comma-list). Python module plugins are
not subject to the trust list because they are already installed in the
host process's site-packages.

Failure modes:

- Plugin import failure -> logged, recorded, **non-fatal** to server boot.
- Subprocess plugin not on the trust list -> recorded as `not_trusted`,
  non-fatal.
- Subprocess plugin spawn failure -> recorded as `spawn_failed`, non-fatal.

`datasphere_connectivity_plugins_status` returns the registry's view of
every configured spec — `ok`, `import_failed`, `not_trusted`,
`spawn_failed` — so an operator can diagnose plugin issues without reading
the audit log.

---

## 10. Threading and concurrency

The 1.0 server is single-process and async-first. There is no thread pool,
no worker count knob, and no internal queue.

- **`mcp.run(transport="stdio")`** uses asyncio; every tool implementation
  is `async def`.
- **`auth.OAuthClient` guards token refresh with an `asyncio.Lock`.** Without
  the lock, a burst of concurrent tool calls would each independently
  refresh the access token. The lock ensures only one refresh is in flight;
  callers waiting on the lock receive the newly-minted token without doing
  their own refresh.
- **`httpx.AsyncClient` is per-request lifecycle.** A new client is built
  for each Datasphere call and closed when the call returns. This adds a TLS
  handshake to every call — measurable, but small in absolute terms — and
  trades it for radically simpler lifecycle. A pooled `AsyncClient` held on
  `DatasphereClient` was considered and explicitly deferred; it is a 1.1
  candidate if benchmarks show the handshake cost is hurting interactive
  tool latency.
- **`cache.TTLCache` is in-process and uses `asyncio.Lock` for write
  serialisation.** Reads are lock-free. The cache covers metadata only
  (spaces, asset lists, `$metadata` documents) — never query results.
- **HTTP transport** is the only place where genuinely concurrent inbound
  requests are possible. Because every layer is async and stateless except
  for the token cache, this works without further coordination.

There is no `multiprocessing`, no `concurrent.futures`, and no background
task scheduler. Anything that looks like a background task in v0.3.x has
been pulled forward into request-time execution for 1.0.

---

## 11. Compatibility matrix

| Component | Floor | Notes |
|---|---|---|
| Python | **3.11+** | Bumped from 3.10 in v0.3.x. Aligns with sibling `SAPBDCMCP`. `match` statements and `Self` types used. |
| `mcp[cli]` | **>=1.25.0, <2** | Required for `ToolAnnotations`, `outputSchema`, structured content, and the prompts/resources spec used. |
| `httpx` | `>=0.27.0` | Per-request async client. |
| `pydantic` | `>=2.7.0` | Argument validation on every tool. |
| `python-dotenv` | `>=1.0.1` | `.env` loader for the new `.env.example` flow. |
| `jsonschema` | `>=4.20.0` | Validates `outputSchema` documents at load time. |
| SAP Datasphere wave | **2025.19+** | First wave where `/api/v1/datasphere/consumption/catalog/*` is available. Older waves run via `DATASPHERE_API_PATH_LEGACY=1`. |
| SAP Integration Suite MCP Gateway | optional | Recommended deployment path for API Policy v4 alignment; the server runs unchanged behind it. |
| OS | Linux / macOS / Windows | CI runs Ubuntu and Windows. |
| MCP hosts tested | Claude Desktop, Cursor, LibreChat, MCP Inspector | Used as the manual verification surface for prompts and resources. |

The license is **PolyForm Noncommercial 1.0.0** starting with 1.0.0. v0.3.1
and earlier remain MIT for users who already have those downloads. The
sibling `SAPBDCMCP` carries the same license; commercial use of either
requires a separate licence.

---

## 12. Where to look next

- **What ships in 1.0 and why** — [`ProjectPlan_v1.0.md`](./ProjectPlan_v1.0.md).
- **Migration from v0.3.x** — `docs/MIGRATION_v0.3_to_v1.0.md` (to be added
  during implementation).
- **API Policy posture** — `docs/SAP_API_POLICY.md` (to be added).
- **The 24-tool catalog** — `ProjectPlan_v1.0.md` section 6.1.
- **The 22 implementations themselves** — `src/sap_datasphere_mcp/tools/tasks.py`
  (carried over from v0.3.1, unchanged in 1.0).
- **Historical v0.3 architecture** — `docs/Architecture.md`. Preserved for
  reference; this document supersedes it for v1.x.
