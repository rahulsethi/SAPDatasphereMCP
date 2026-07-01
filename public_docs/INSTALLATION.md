# Installation

Three ways to install. Pick the one that matches your stack.

---

## Option 1 — uvx (recommended)

The fastest way to try the server. `uvx` runs it in an isolated environment, no pip install required.

```bash
uvx mcp-sap-datasphere-server
```

What you get: the latest published version, installed on demand, with no impact on your global Python. Re-run the same command later and you get the latest release.

## Option 2 — pip

If you want the server installed into a Python environment you control:

```bash
pip install mcp-sap-datasphere-server
```

What you get: the `sap-datasphere-mcp` console script on your PATH and the package importable for scripting.

## Option 3 — npx

If your team lives in Node-land:

```bash
npx -y @rahulsethi/sap-datasphere-mcp
```

What you get: a thin npm wrapper that downloads and launches the Python server for you. Node 18+ required.

---

## Prerequisites

| If you use… | You need… |
|---|---|
| `uvx` or `pip` | Python **3.11+** |
| `npx` | Node **18+** (and Python 3.11+ on PATH — the wrapper invokes Python under the hood) |
| Any option, real tenant | An SAP Datasphere tenant with a **technical OAuth client** (Client ID + Client Secret) |

You can skip the tenant entirely for your first run — see *Mock mode* below.

---

## Configure credentials

The server is configured entirely through environment variables.

### Required

| Variable | What it is |
|---|---|
| `DATASPHERE_TENANT_URL` | Your tenant's base URL, e.g. `https://my-tenant.eu10.hcs.cloud.sap` |
| `DATASPHERE_OAUTH_TOKEN_URL` | The OAuth token endpoint your tenant gave you |
| `DATASPHERE_CLIENT_ID` | OAuth client ID for the technical user |
| `DATASPHERE_CLIENT_SECRET` | OAuth client secret |

### Optional

| Variable | Default | What it does |
|---|---|---|
| `DATASPHERE_VERIFY_TLS` | `1` | Verify TLS certificates. Set to `0` only for non-production tenants with self-signed certs. |
| `DATASPHERE_MOCK_MODE` | `0` | When `1`, returns realistic sample data and never calls your tenant. Great for demos and first runs. |
| `DATASPHERE_API_PATH_LEGACY` | `0` | When `1`, uses the older v0.3-era API path layout. Most tenants don't need this. |
| `DATASPHERE_AUDIT_ENABLED` | `0` | When `1`, writes a local audit trail of tool calls (used by `datasphere_governance_audit_tail`). |

### Setting them — PowerShell

```powershell
$env:DATASPHERE_TENANT_URL      = "https://my-tenant.eu10.hcs.cloud.sap"
$env:DATASPHERE_OAUTH_TOKEN_URL = "https://my-tenant.authentication.eu10.hana.ondemand.com/oauth/token"
$env:DATASPHERE_CLIENT_ID       = "sb-xxxx"
$env:DATASPHERE_CLIENT_SECRET   = "yyyy"
```

### Setting them — bash / zsh

```bash
export DATASPHERE_TENANT_URL="https://my-tenant.eu10.hcs.cloud.sap"
export DATASPHERE_OAUTH_TOKEN_URL="https://my-tenant.authentication.eu10.hana.ondemand.com/oauth/token"
export DATASPHERE_CLIENT_ID="sb-xxxx"
export DATASPHERE_CLIENT_SECRET="yyyy"
```

---

## Mock mode — try it without a tenant

No tenant yet? No problem. Set:

```bash
export DATASPHERE_MOCK_MODE=1
```

Now every tool returns realistic sample data — spaces, assets, columns, profiles, the lot. You can wire the server into Claude Desktop, try every tool, build a demo, and never touch a real tenant. When you're ready, unset the variable and supply real credentials.

---

## Verify your install

```bash
sap-datasphere-mcp --version
sap-datasphere-mcp --help
```

For a one-shot "is the server breathing" test (this starts the MCP stdio server; press `Ctrl+C` to stop):

```bash
sap-datasphere-mcp
```

You should see a JSON log line announcing the server is up. That's it — the server is now waiting for an MCP client to talk to it.

---

## Wire to Claude Desktop

Open Claude Desktop's `claude_desktop_config.json` (Settings → Developer → Edit Config) and add:

```json
{
  "mcpServers": {
    "sap-datasphere": {
      "command": "uvx",
      "args": ["mcp-sap-datasphere-server"],
      "env": {
        "DATASPHERE_TENANT_URL": "https://my-tenant.eu10.hcs.cloud.sap",
        "DATASPHERE_OAUTH_TOKEN_URL": "https://my-tenant.authentication.eu10.hana.ondemand.com/oauth/token",
        "DATASPHERE_CLIENT_ID": "sb-xxxx",
        "DATASPHERE_CLIENT_SECRET": "yyyy"
      }
    }
  }
}
```

Restart Claude Desktop. The Datasphere tools will appear in the tool picker.

---

## Wire to Cursor

Create or edit `.cursor/mcp.json` in your project:

```json
{
  "mcpServers": {
    "sap-datasphere": {
      "command": "uvx",
      "args": ["mcp-sap-datasphere-server"],
      "env": {
        "DATASPHERE_TENANT_URL": "https://my-tenant.eu10.hcs.cloud.sap",
        "DATASPHERE_OAUTH_TOKEN_URL": "https://my-tenant.authentication.eu10.hana.ondemand.com/oauth/token",
        "DATASPHERE_CLIENT_ID": "sb-xxxx",
        "DATASPHERE_CLIENT_SECRET": "yyyy"
      }
    }
  }
}
```

Reload Cursor. The server appears under the MCP panel.

---

## Wire to other MCP hosts

The server speaks the standard MCP stdio transport, so any compliant host can launch it the same way: a `command` (e.g. `uvx`), `args` (`["mcp-sap-datasphere-server"]`), and an `env` block with your credentials. Check your host's MCP documentation for the exact config file location.

---

## HTTP transport (optional)

For remote deployments, the server can speak HTTP instead of stdio:

```bash
export DATASPHERE_MCP_BEARER_TOKEN="a-strong-shared-secret"
sap-datasphere-mcp --transport http --host 0.0.0.0 --port 8080
```

| Variable | What it does |
|---|---|
| `DATASPHERE_MCP_BEARER_TOKEN` | Required bearer token. Clients must send `Authorization: Bearer <token>`. |

Use this when you want a single shared MCP server inside a VPC or container rather than a per-user stdio process. For enterprise SAP customers, we recommend fronting this with the **Integration Suite MCP Gateway** — see [SAP_API_POLICY.md](../SAP_API_POLICY.md).
