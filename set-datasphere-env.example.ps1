# SAP Datasphere MCP Server
# File: set-datasphere-env.example.ps1
#
# Template for local environment variables. Copy this to `set-datasphere-env.ps1`
# (which is gitignored) and fill in real values. Dot-source it before running
# the server or any example script:
#
#   Copy-Item set-datasphere-env.example.ps1 set-datasphere-env.ps1
#   # ... edit set-datasphere-env.ps1 with your credentials ...
#   . .\set-datasphere-env.ps1

$env:DATASPHERE_TENANT_URL      = 'https://<your-tenant>.<region>.hcs.cloud.sap'
$env:DATASPHERE_OAUTH_TOKEN_URL = 'https://<your-uaa-domain>/oauth/token'
$env:DATASPHERE_CLIENT_ID       = '<your-client-id>'
$env:DATASPHERE_CLIENT_SECRET   = '<your-client-secret>'

# Optional: disable TLS verification for self-signed corporate proxies.
# $env:DATASPHERE_VERIFY_TLS = '0'

# Optional: run against the in-memory mock dataset instead of a real tenant.
# $env:DATASPHERE_MOCK_MODE = '1'

Write-Host "Datasphere environment variables set."