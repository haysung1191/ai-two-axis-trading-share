from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

import scripts.compare_btc_1d_post_spike_window2_gate_diagnostic as mod


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_window2_gate_diagnostic_counts_blockers(tmp_path: Path, monkeypatch) -> None:
    _write_json(
        tmp_path / "btc_1d_post_spike_idle_window_context_latest.json",
        {
            "window_2_reference": {
                "timestamp_start": "2021-01-03T00:00:00+00:00",
                "timestamp_end": "2021-01-06T00:00:00+00:00",
            }
        },
    )

    idx = pd.date_range("2020-12-20", periods=30, freq="1d", tz="UTC")
    close = pd.Series([100 + i for i in range(30)], index=idx, dtype=float)
    frame = pd.DataFrame(index=idx)
    frame["open"] = close
    frame["high"] = close + 1
    frame["low"] = close - 1
    frame["close"] = close
    frame["volume"] = 1000.0

    monkeypatch.setattr(mod, "_load_ohlcv", lambda periods=2200: frame)

    report = mod.build_report(analysis_dir=tmp_path)

    assert report["window_2_range"]["timestamp_start"] == "2021-01-03T00:00:00+00:00"
    assert len(report["compared_variants"]) == 2
    assert "primary_blocker_gate" in report["gate_diagnostic_verdict"]
