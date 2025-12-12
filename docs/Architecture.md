
---

## 3. `Architecture.md` (v3)

```markdown
<!-- SAP Datasphere MCP Server -->
<!-- File: Architecture.md -->
<!-- Version: v3 -->

# Architecture – SAP Datasphere MCP Server

This document describes the architecture and main design decisions of the SAP Datasphere MCP Server.

The goal of this server is to expose **SAP Datasphere** metadata and data (preview/query) as **Model Context Protocol (MCP) tools**, so an AI agent (e.g. DevAssist) can explore spaces, discover assets, and sample data safely via OAuth.

---

## 1. High-Level Overview

At a high level:

- A **client** (ChatGPT / DevAssist / MCP inspector) connects to the MCP server over **STDIO**.
- The MCP server exposes a set of **tools** (current surface):
  - `datasphere_ping`
  - `datasphere_list_spaces`
  - `datasphere_list_assets`
  - `datasphere_preview_asset`
  - `datasphere_describe_asset_schema`
  - `datasphere_query_relational`
- Each tool calls into a small **task layer**, which:
  - Builds a `DatasphereClient` from environment config.
  - Uses **OAuth** to obtain an access token.
  - Calls SAP Datasphere **Catalog** and **Consumption** REST APIs.
- The results are normalised into **LLM-friendly JSON** (lists of dicts plus simple `meta` objects).

All of this is packaged as a Python project with a console entry point:

```bash
sap-datasphere-mcp
