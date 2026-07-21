from datetime import datetime
from pathlib import Path
import types

import pandas as pd

from live_core import kis_runtime


def test_build_output_filename_uses_mode_prefix() -> None:
    now = datetime(2026, 4, 16, 9, 30)
    assert kis_runtime.build_output_filename(etf_mode=False, now=now) == "momentum_results_20260416_0930.xlsx"
    assert kis_runtime.build_output_filename(etf_mode=True, now=now) == "etf_results_20260416_0930.xlsx"


def test_run_screener_cli_saves_to_local_desktop(tmp_path: Path) -> None:
    env = {"USERPROFILE": str(tmp_path), "SCREENER_MODE": "ETF"}
    desktop = tmp_path / "Desktop"
    desktop.mkdir()

    def fake_runner(*, etf_mode: bool = False, config_module=None):
        assert etf_mode is True
        return pd.DataFrame([{"Code": "069500", "Name": "ETF"}])

    fake_config = types.SimpleNamespace(GCS_BUCKET_NAME=None)
    original_to_excel = pd.DataFrame.to_excel

    def fake_to_excel(self, path, index=False):
        Path(path).write_text("ok", encoding="utf-8")

    pd.DataFrame.to_excel = fake_to_excel
    try:
        saved_path = kis_runtime.run_screener_cli(
            screening_runner=fake_runner,
            env=env,
            config_module=fake_config,
            now=datetime(2026, 4, 16, 9, 30),
        )
    finally:
        pd.DataFrame.to_excel = original_to_excel

    assert saved_path is not None
    assert Path(saved_path).name == "etf_results_20260416_0930.xlsx"
    assert Path(saved_path).exists()
