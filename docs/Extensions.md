<!-- SAP Datasphere MCP Server -->
<!-- File: Extensions.md -->
<!-- Version: v2 -->

# Extensions & Plugin Model – SAP Datasphere MCP Server

This document describes how the SAP Datasphere MCP Server can be **extended** beyond its open-core features.

The design goal is simple:

> Keep the **core** small, stable, and open-source, while allowing **extensions** (including commercial ones) to plug in without forking.

---

## 1. Extension Types

There are three main ways to extend the server:

1. **New core tools** (inside this repo, open-core).
2. **Plugins** (separate modules / packages that register tools).
3. **New transports or wrappers** (e.g. HTTP server, IDE integration).

The rest of this document focuses on tools and plugins.

---

## 2. Adding New Core Tools

Core tools live in `sap_datasphere_mcp.tools.tasks`.

To add a new core tool:

1. Implement an async “task” function:

   ```python
   async def my_new_task(arg1: str, limit: int = 20) -> dict:
       client = _make_client()
       # call DatasphereClient methods, apply limits, shape JSON
       return {"result": "..."}
   ```

2. Register it with the MCP server in `register_tools(server)`:

   ```python
   @server.tool(
       name="datasphere_my_new_tool",
       description="Explain briefly what this does.",
   )
   async def mcp_my_new_tool(arg1: str, limit: int = 20) -> dict:
       return await my_new_task(arg1=arg1, limit=limit)
   ```

3. Add tests under `tests/` and (optionally) example prompts in the `TestPrompts` document.

Core tools should:

- respect global **limits** (row counts, etc.),
- only call **read-only** Datasphere APIs,
- return small, predictable JSON structures suitable for LLMs.

---

## 3. Plugin Model (v0.3+)

Starting in v0.3, the server supports **plugins**:

- Plugins are modules that export a `register_tools(server)` function.
- At startup, the server reads a list of plugin modules from an environment variable (e.g. `DATASPHERE_PLUGINS`).
- For each module, it tries to import it and call its `register_tools(server)` function.

Example env configuration:

```bash
export DATASPHERE_PLUGINS="sap_datasphere_mcp.plugins.analytics,sap_datasphere_mcp.plugins.rag"
```

### 3.1 Plugin Lifecycle

1. The stdio server starts and creates a `server` instance.
2. It registers **core tools** via `sap_datasphere_mcp.tools.tasks.register_tools(server)`.
3. It calls `sap_datasphere_mcp.plugins.registry.register_plugins(server)`:
   - Reads `DATASPHERE_PLUGINS`.
   - Imports each module.
   - Calls `module.register_tools(server)`.

If any plugin fails to load:

- the error is logged,
- the server continues running with remaining plugins,
- diagnostics can show which plugins did or didn’t load.

### 3.2 Plugin Structure

A minimal plugin module might look like this:

```python
# sap_datasphere_mcp/plugins/analytics.py

from typing import Any, Dict
from ..tools.tasks import preview_asset, query_relational

def register_tools(server: Any) -> None:
    @server.tool(
        name="datasphere_compare_assets_basic",
        description="Compare row counts and basic stats for two assets.",
    )
    async def mcp_compare_assets_basic(
        space_id: str,
        asset_a: str,
        asset_b: str,
        top: int = 100,
    ) -> Dict[str, Any]:
        # Example: call existing core tools
        result_a = await preview_asset(space_id=space_id, asset_name=asset_a, top=top)
        result_b = await preview_asset(space_id=space_id, asset_name=asset_b, top=top)
        # shape the comparison result
        return {
            "asset_a": {"meta": result_a.get("meta"), "row_count": len(result_a.get("rows", []))},
            "asset_b": {"meta": result_b.get("meta"), "row_count": len(result_b.get("rows", []))},
        }
```

Notes:

- Plugins **reuse** core task functions rather than duplicating HTTP logic.
- Plugins may add orchestration / macros, but should still respect limits and safety constraints.

---

## 4. Open-Core vs Plugins (Conceptual)

Without getting into product/licensing details, the top-level principle is:

- **Open-core**:
  - Contains transports, config, and all basic Datasphere exploration features.
  - Includes simple analytical queries and basic summaries.
  - Remains in this public repo.

- **Plugins**:
  - Live in separate modules (possibly separate packages).
  - Use `register_tools(server)` to attach extra tools.
  - Can focus on heavier workloads or opinionated workflows:
    - Advanced OLAP analysis,
    - RAG & semantic search,
    - governance dashboards,
    - enterprise deployment bundles.

From the server’s point of view, both are just tools attached to the same MCP surface.

---

## 5. Extensibility Guidelines

When adding new tools (core or plugin):

1. **Stay read-only**  
   Avoid anything that changes state in Datasphere (users, roles, DDL, ETL exports).

2. **Be explicit about cost**  
   - Tools that can be expensive should:
     - document their cost in the description,
     - enforce hard limits,
     - expose optional parameters to narrow scope.

3. **Return simple JSON**  
   - Prefer:
     - lists of rows/objects,
     - small `meta` dicts,
     - clearly named fields.
   - Avoid deeply nested, hard-to-interpret shapes.

4. **Compose existing tools**  
   - For higher-level behaviours, orchestrate existing tasks rather than re-implementing low-level API calls.

5. **Document prompts**  
   - When you add a new tool, record a few example prompts in the test prompts file so humans/LLMs know how to trigger it.

---

## 6. Future Extension Areas (High-Level)

These ideas live in the backlog and are likely future plugin themes:

- **Advanced analytical / OLAP macros**
  - multi-step analysis workflows, trend comparisons, what-if scenarios.

- **Data Products & governance**
  - data product explorers, lineage views, ownership & SLA views.

- **RAG & unstructured data**
  - vector search and semantic retrieval anchored on Datasphere/HANA storage.

- **Operations bundles**
  - observability, metrics, rate limits, and enterprise deployment templates.

All of them can be layered on top of the plugin model introduced in v0.3, without destabilising the open-core server.