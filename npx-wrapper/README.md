# @rahulsethi/sap-datasphere-mcp (npm wrapper)

A tiny Node bootstrap that lets you run the **SAP Datasphere MCP Server**
without installing Python tooling first. The real implementation is the
Python package [`sap-datasphere-mcp`](https://pypi.org/project/sap-datasphere-mcp/)
in this same repo; this wrapper just probes for a Python launcher and hands
off stdio.

## Why this exists

MCP hosts like Claude Desktop and Cursor make `npx`-launched servers very
easy to wire up. This wrapper lets users get started with one line:

```json
{
  "mcpServers": {
    "sap-datasphere": {
      "command": "npx",
      "args": ["-y", "@rahulsethi/sap-datasphere-mcp"],
      "env": {
        "DATASPHERE_TENANT_URL": "https://...",
        "DATASPHERE_OAUTH_TOKEN_URL": "https://.../oauth/token",
        "DATASPHERE_CLIENT_ID": "...",
        "DATASPHERE_CLIENT_SECRET": "..."
      }
    }
  }
}
```

## How it works

On invocation, the wrapper picks the first available Python launcher from:

1. `uvx mcp-sap-datasphere-server` — recommended (`uv` is the fastest path)
2. `pipx run mcp-sap-datasphere-server`
3. `python -m sap_datasphere_mcp` (or `python3` on POSIX)

It then forwards stdio to the chosen process. SIGINT / SIGTERM / SIGHUP are
forwarded too so MCP hosts can shut the server down cleanly. If no launcher
is on PATH, the wrapper exits non-zero with an actionable error.

## See also

- Main repo: https://github.com/rahulsethi/SAPDatasphereMCP
- Sibling product: https://github.com/rahulsethi/SAPBDCMCP
- Install docs: https://github.com/rahulsethi/SAPDatasphereMCP/blob/main/public_docs/INSTALLATION.md

## License

Business Source License 1.1 (BSL 1.1) — same terms as the Python package. See the
repository root [`LICENSE`](../LICENSE) and
[`COMMERCIAL_LICENSING.md`](../COMMERCIAL_LICENSING.md).
