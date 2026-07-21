from __future__ import annotations

import json
from pathlib import Path

from scripts.summarize_btc_1d_attack_common_rules import AttackArtifact, build_attack_common_rules, write_outputs


def _write_batch(path: Path, results: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"results": results}, ensure_ascii=False, indent=2), encoding="utf-8")


def test_build_attack_common_rules_summarizes_leader_parameter_ranges(tmp_path: Path) -> None:
    a = tmp_path / "a.json"
    b = tmp_path / "b.json"
    c = tmp_path / "c.json"
    _write_batch(
        a,
        [
            {
                "strategy_name": "a1",
                "variant_label": "leader_a",
                "decision": "KEEP",
                "cagr": 0.31,
                "max_drawdown": 0.19,
                "sharpe": 1.2,
                "trades": 20,
                "completed_trades": 10,
                "parameters": {"trend_ema_window": 72, "min_atr_expansion_ratio": 1.12, "max_hold_bars": 34, "min_volume_ratio": 1.06},
            }
        ],
    )
    _write_batch(
        b,
        [
            {
                "strategy_name": "b1",
                "variant_label": "leader_b",
                "decision": "KEEP",
                "cagr": 0.28,
                "max_drawdown": 0.17,
                "sharpe": 1.15,
                "trades": 18,
                "completed_trades": 9,
                "parameters": {"trend_ema_window": 84, "min_atr_expansion_ratio": 1.18, "max_hold_bars": 36, "min_volume_ratio": 1.10},
            }
        ],
    )
    _write_batch(
        c,
        [
            {
                "strategy_name": "c1",
                "variant_label": "leader_c",
                "decision": "KEEP",
                "cagr": 0.24,
                "max_drawdown": 0.16,
                "sharpe": 1.05,
                "trades": 16,
                "completed_trades": 8,
                "parameters": {"trend_ema_window": 84, "min_atr_expansion_ratio": 1.15, "max_hold_bars": 34, "min_volume_ratio": 1.08},
            }
        ],
    )

    payload = build_attack_common_rules(
        artifacts=(
            AttackArtifact("fam_a", a),
            AttackArtifact("fam_b", b),
            AttackArtifact("fam_c", c),
        )
    )

    assert payload["leader_count"] == 3
    assert payload["recommended_attack_rule_seed"]["trend_ema_window"] == 84.0
    assert payload["recommended_attack_rule_seed"]["min_atr_expansion_ratio"] == 1.15
    assert payload["parameter_ranges"]["max_hold_bars"]["min"] == 34.0
    assert payload["parameter_ranges"]["max_hold_bars"]["max"] == 36.0
    assert payload["priority_hints"]


def test_write_outputs_creates_latest_aliases(tmp_path: Path) -> None:
    payload = {
        "generated_at": "20260419T133500Z",
        "leader_count": 1,
        "leaders": [],
        "priority_hints": [],
        "parameter_ranges": {},
        "recommended_attack_rule_seed": {},
    }

    artifacts = write_outputs(payload, analysis_dir=tmp_path)

    assert Path(artifacts["json"]).exists()
    assert Path(artifacts["latest_json"]).exists()
    assert Path(artifacts["txt"]).exists()
    assert Path(artifacts["latest_txt"]).exists()
