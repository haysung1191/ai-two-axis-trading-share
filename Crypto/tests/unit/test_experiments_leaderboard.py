import json
from pathlib import Path

from app.domains.experiments.leaderboard import build_leaderboard


def test_leaderboard_ranks_by_sharpe_then_cagr_then_drawdown(tmp_path: Path) -> None:
    artifacts = tmp_path / "artifacts"
    run_a = artifacts / "run-a"
    run_b = artifacts / "run-b"
    run_c = artifacts / "run-c"
    for run_dir in [run_a, run_b, run_c]:
        run_dir.mkdir(parents=True, exist_ok=True)

    (run_a / "backtest_report.json").write_text(
        json.dumps(
            {"strategy_name": "s1", "sharpe": 1.1, "cagr": 0.1, "max_drawdown": 0.2, "win_rate": 0.5, "trades": 20}
        ),
        encoding="utf-8",
    )
    (run_b / "backtest_report.json").write_text(
        json.dumps(
            {"strategy_name": "s2", "sharpe": 1.3, "cagr": 0.05, "max_drawdown": 0.3, "win_rate": 0.45, "trades": 15}
        ),
        encoding="utf-8",
    )
    (run_c / "backtest_report.json").write_text(
        json.dumps(
            {"strategy_name": "s3", "sharpe": 1.3, "cagr": 0.2, "max_drawdown": 0.25, "win_rate": 0.55, "trades": 18}
        ),
        encoding="utf-8",
    )

    result = build_leaderboard(artifacts_root=artifacts)
    entries = result["entries"]
    assert entries[0]["run_id"] == "run-c"
    assert entries[1]["run_id"] == "run-b"
    assert entries[2]["run_id"] == "run-a"

