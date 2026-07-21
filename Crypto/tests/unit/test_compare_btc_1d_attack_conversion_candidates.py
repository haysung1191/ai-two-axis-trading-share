from __future__ import annotations

import json
from pathlib import Path

from scripts.compare_btc_1d_attack_conversion_candidates import (
    CandidateArtifact,
    build_attack_conversion_screen,
)


def _write_payload(path: Path, strategy_name: str, variant_label: str, cagr: float, mdd: float, sharpe: float) -> None:
    payload = {
        "results": [
            {
                "strategy_name": strategy_name,
                "variant_label": variant_label,
                "decision": "KEEP",
                "sharpe": sharpe,
                "cagr": cagr,
                "max_drawdown": mdd,
                "win_rate": 0.5,
                "trades": 20,
                "completed_trades": 10,
                "failed_gates": [],
                "parameters": {},
            }
        ]
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_build_attack_conversion_screen(tmp_path: Path) -> None:
    attackish = tmp_path / "attackish.json"
    defensive = tmp_path / "defensive.json"
    kill = tmp_path / "kill.json"
    _write_payload(attackish, "s1", "v1", 0.38, 0.28, 1.2)
    _write_payload(defensive, "s2", "v2", 0.24, 0.16, 1.1)
    _write_payload(kill, "s3", "v3", 0.12, 0.08, 0.9)

    result = build_attack_conversion_screen(
        analysis_results_dir=tmp_path,
        artifacts=(
            CandidateArtifact("attack_family", attackish),
            CandidateArtifact("defensive_family", defensive),
            CandidateArtifact("kill_family", kill),
        ),
    )

    assert result["summary"]["top_attack_conversion_candidate"] == "attack_family"
    assert result["summary"]["best_defensive_hold"] == "defensive_family"
    assert "kill_family" in result["summary"]["attack_conversion_nonstarters"]
    assert Path(result["analysis_result_json"]).exists()
    assert Path(result["analysis_result_md"]).exists()
