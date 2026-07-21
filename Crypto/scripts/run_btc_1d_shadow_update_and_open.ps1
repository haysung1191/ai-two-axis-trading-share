$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
$updateScript = Join-Path $repoRoot "scripts\run_btc_1d_shadow_update.py"
$briefPath = Join-Path $repoRoot "analysis_results\btc_1d_operating_brief_md_latest.md"
$indexPath = Join-Path $repoRoot "analysis_results\btc_1d_operating_index_md_latest.md"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Python virtual environment not found at $python"
}

& $python $updateScript
if ($LASTEXITCODE -ne 0) {
    throw "Shadow update failed with exit code $LASTEXITCODE"
}

if (Test-Path -LiteralPath $briefPath) {
    Start-Process -FilePath $briefPath | Out-Null
}
if (Test-Path -LiteralPath $indexPath) {
    Start-Process -FilePath $indexPath | Out-Null
}
