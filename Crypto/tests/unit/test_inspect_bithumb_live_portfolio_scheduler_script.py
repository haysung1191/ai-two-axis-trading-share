from __future__ import annotations

from pathlib import Path


SCRIPT_PATH = Path(r"C:\AI\Crypto\deploy\windows\inspect_bithumb_live_portfolio_scheduler.ps1")


def test_scheduler_inspect_script_queries_task_state_and_runtime() -> None:
    content = SCRIPT_PATH.read_text(encoding="utf-8")

    assert '$TaskName = "BithumbLivePortfolioManager"' in content
    assert 'Get-ScheduledTask -TaskName $TaskName' in content
    assert 'Get-ScheduledTaskInfo -TaskName $TaskName' in content
    assert 'task.exists=True' in content
    assert 'task.last_result={0}' in content
