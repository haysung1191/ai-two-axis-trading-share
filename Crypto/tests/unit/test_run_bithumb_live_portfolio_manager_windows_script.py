from __future__ import annotations

from pathlib import Path


SCRIPT_PATH = Path(r"C:\AI\Crypto\deploy\windows\run_bithumb_live_portfolio_manager.ps1")


def test_runner_script_updates_status_snapshot_after_inspect() -> None:
    content = SCRIPT_PATH.read_text(encoding="utf-8")

    assert '$StatusScriptPath = Join-Path $ProjectRoot "deploy\\windows\\inspect_bithumb_live_portfolio_status.ps1"' in content
    assert "& powershell -ExecutionPolicy Bypass -File $InspectScriptPath" in content
    assert "& powershell -ExecutionPolicy Bypass -File $StatusScriptPath -IncludeRuns" in content
    assert content.index("& powershell -ExecutionPolicy Bypass -File $InspectScriptPath") < content.index(
        "& powershell -ExecutionPolicy Bypass -File $StatusScriptPath -IncludeRuns"
    )
