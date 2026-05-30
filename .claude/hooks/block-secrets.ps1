# PreToolUse hook: block writes/reads to files holding live SAP Datasphere secrets.
# Exit code 2 blocks the tool call and feeds stderr back to Claude as the reason.
$raw = [Console]::In.ReadToEnd()
try { $data = $raw | ConvertFrom-Json } catch { exit 0 }

$path = $data.tool_input.file_path
if (-not $path) { exit 0 }

$leaf = Split-Path $path -Leaf

# The committed template is always safe to touch.
if ($leaf -eq 'set-datasphere-env.example.ps1') { exit 0 }

# Block the real secret env files (git-ignored): set-datasphere-env.ps1 and .env*
if ($leaf -eq 'set-datasphere-env.ps1' -or $leaf -match '^\.env') {
    [Console]::Error.WriteLine("Blocked: '$leaf' holds live SAP Datasphere OAuth secrets (git-ignored). Edit set-datasphere-env.example.ps1 instead, or ask the user to change credentials manually.")
    exit 2
}

exit 0
