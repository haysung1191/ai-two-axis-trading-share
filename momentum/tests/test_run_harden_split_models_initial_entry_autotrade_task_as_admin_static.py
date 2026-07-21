from pathlib import Path


def test_admin_launcher_ps1_contains_runas() -> None:
    path = Path(r"C:\AI\momentum\tools\analysis\run_harden_split_models_initial_entry_autotrade_task_as_admin.ps1")
    text = path.read_text(encoding="utf-8")

    assert "Start-Process powershell -Verb RunAs" in text
    assert "harden_split_models_initial_entry_autotrade_task.ps1" in text
    assert "show_split_models_initial_entry_autotrade_task_status.ps1" in text
    assert "verify_split_models_initial_entry_operational_readiness.ps1" in text
    assert "build_split_models_initial_entry_operational_handoff.ps1" in text
    assert "autotrade_task_status_latest.json" in text
    assert "autotrade_task_status_latest.txt" in text
    assert 'autotrade_task_status_{0}.json' in text
    assert 'autotrade_task_status_{0}.txt' in text
    assert "operational_readiness_latest.json" in text
    assert "operational_readiness_latest.txt" in text
    assert 'operational_readiness_{0}.json' in text
    assert 'operational_readiness_{0}.txt' in text
    assert "operational_handoff_latest.json" in text
    assert "operational_handoff_latest.txt" in text
    assert 'operational_handoff_{0}.json' in text
    assert 'operational_handoff_{0}.txt' in text


def test_admin_launcher_bat_calls_ps1() -> None:
    path = Path(r"C:\AI\momentum\tools\analysis\run_harden_split_models_initial_entry_autotrade_task_as_admin.bat")
    text = path.read_text(encoding="utf-8")

    assert "run_harden_split_models_initial_entry_autotrade_task_as_admin.ps1" in text
