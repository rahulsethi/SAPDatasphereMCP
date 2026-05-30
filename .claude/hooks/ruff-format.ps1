# PostToolUse hook: format + autofix edited Python files with ruff.
# Receives the tool-call JSON on stdin; acts only on *.py files that exist.
$ErrorActionPreference = 'SilentlyContinue'

$raw = [Console]::In.ReadToEnd()
try { $data = $raw | ConvertFrom-Json } catch { exit 0 }

$path = $data.tool_input.file_path
if (-not $path) { exit 0 }
if ($path -notmatch '\.py$') { exit 0 }
if (-not (Test-Path $path)) { exit 0 }

# Prefer the project venv's ruff, fall back to whatever is on PATH.
$ruff = Join-Path $PWD '.venv\Scripts\ruff.exe'
if (-not (Test-Path $ruff)) { $ruff = 'ruff' }

try {
    & $ruff format "$path"        2>&1 | Out-Null
    & $ruff check --fix "$path"   2>&1 | Out-Null
} catch { }

exit 0
