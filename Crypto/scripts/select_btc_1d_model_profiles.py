from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _utc_timestamp() -> str:
    return datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _score_attack(candidate: dict[str, Any]) -> float:
    cagr = float(candidate.get("cagr") or 0.0)
    mdd = float(candidate.get("mdd") or 1.0)
    sharpe = float(candidate.get("sharpe") or 0.0)
    drift = float(candidate.get("drift") or 0.0)
    return cagr - (0.30 * mdd) + (0.05 * sharpe) - (0.10 * drift)


def _score_operating(candidate: dict[str, Any]) -> float:
    cagr = float(candidate.get("cagr") or 0.0)
    mdd = float(candidate.get("mdd") or 1.0)
    sharpe = float(candidate.get("sharpe") or 0.0)
    drift = float(candidate.get("drift") or 0.0)
    return (-1.0 * mdd) + (0.35 * cagr) + (0.05 * sharpe) - (0.10 * drift)


def _candidate_read(candidate: dict[str, Any]) -> str:
    return (
        f"{candidate['label']} | cagr={candidate.get('cagr', 0.0):.4f} | "
        f"mdd={candidate.get('mdd', 0.0):.4f} | sharpe={candidate.get('sharpe', 0.0):.4f} | "
        f"drift={candidate.get('drift', 0.0):.4f}"
    )


def build_model_profile_selection(*, analysis_dir: Path) -> dict[str, Any]:
    practical = _load_json(analysis_dir / "btc_1d_practical_scorecard_latest.json")
    research = _load_json(analysis_dir / "btc_1d_research_stack_operating_brief_latest.json")
    operating_index = _load_json(analysis_dir / "btc_1d_operating_index_latest.json")

    practical_summary = practical.get("summary", {})
    practical_carry = practical_summary.get("carry_metrics", {})
    practical_walk_forward = practical.get("walk_forward_check", {}).get("oos_metrics", {})
    practical_friction = practical_summary.get("friction_20bps_metrics", {})

    research_models = research.get("models", {})

    candidates = [
        {
            "label": str(practical.get("candidate") or "practical_candidate"),
            "role": "operating_practical",
            "source": "practical_scorecard",
            "cagr": _safe_float(practical_carry.get("cagr")),
            "mdd": _safe_float(practical_carry.get("max_drawdown")),
            "sharpe": _safe_float(practical_carry.get("sharpe")),
            "oos_cagr": _safe_float(practical_walk_forward.get("cagr")),
            "oos_mdd": _safe_float(practical_walk_forward.get("max_drawdown")),
            "oos_sharpe": _safe_float(practical_walk_forward.get("sharpe")),
            "drift": _safe_float(practical.get("walk_forward_check", {}).get("sensitivity_max_drift")) or 0.0,
            "friction_cagr": _safe_float(practical_friction.get("cagr")),
            "friction_mdd": _safe_float(practical_friction.get("max_drawdown")),
            "friction_sharpe": _safe_float(practical_friction.get("sharpe")),
        },
        {
            "label": str(research_models.get("attack_main", {}).get("label") or "attack_main"),
            "role": "attack_main",
            "source": "research_stack_operating_brief",
            "cagr": _safe_float(research_models.get("attack_main", {}).get("base_cagr")),
            "mdd": _safe_float(research_models.get("attack_main", {}).get("base_mdd")),
            "sharpe": _safe_float(research_models.get("attack_main", {}).get("base_sharpe")),
            "oos_cagr": _safe_float(research_models.get("attack_main", {}).get("oos_cagr")),
            "oos_mdd": _safe_float(research_models.get("attack_main", {}).get("oos_mdd")),
            "oos_sharpe": _safe_float(research_models.get("attack_main", {}).get("oos_sharpe")),
            "drift": _safe_float(research_models.get("attack_main", {}).get("sensitivity_max_drift")) or 0.0,
            "friction_cagr": _safe_float(research_models.get("attack_main", {}).get("cost20_cagr")),
            "friction_mdd": _safe_float(research_models.get("attack_main", {}).get("cost20_mdd")),
            "friction_sharpe": _safe_float(research_models.get("attack_main", {}).get("cost20_sharpe")),
        },
        {
            "label": str(research_models.get("attack_backup", {}).get("label") or "attack_backup"),
            "role": "attack_backup",
            "source": "research_stack_operating_brief",
            "cagr": _safe_float(research_models.get("attack_backup", {}).get("base_cagr")),
            "mdd": _safe_float(research_models.get("attack_backup", {}).get("base_mdd")),
            "sharpe": _safe_float(research_models.get("attack_backup", {}).get("base_sharpe")),
            "oos_cagr": _safe_float(research_models.get("attack_backup", {}).get("oos_cagr")),
            "oos_mdd": _safe_float(research_models.get("attack_backup", {}).get("oos_mdd")),
            "oos_sharpe": _safe_float(research_models.get("attack_backup", {}).get("oos_sharpe")),
            "drift": _safe_float(research_models.get("attack_backup", {}).get("sensitivity_max_drift")) or 0.0,
            "friction_cagr": _safe_float(research_models.get("attack_backup", {}).get("cost20_cagr")),
            "friction_mdd": _safe_float(research_models.get("attack_backup", {}).get("cost20_mdd")),
            "friction_sharpe": _safe_float(research_models.get("attack_backup", {}).get("cost20_sharpe")),
        },
        {
            "label": str(research_models.get("defensive_hold", {}).get("label") or "defensive_hold"),
            "role": "defensive_hold",
            "source": "research_stack_operating_brief",
            "cagr": _safe_float(research_models.get("defensive_hold", {}).get("base_cagr")),
            "mdd": _safe_float(research_models.get("defensive_hold", {}).get("base_mdd")),
            "sharpe": _safe_float(research_models.get("defensive_hold", {}).get("base_sharpe")),
            "oos_cagr": _safe_float(research_models.get("defensive_hold", {}).get("oos_cagr")),
            "oos_mdd": _safe_float(research_models.get("defensive_hold", {}).get("oos_mdd")),
            "oos_sharpe": _safe_float(research_models.get("defensive_hold", {}).get("oos_sharpe")),
            "drift": _safe_float(research_models.get("defensive_hold", {}).get("sensitivity_max_drift")) or 0.0,
            "friction_cagr": _safe_float(research_models.get("defensive_hold", {}).get("cost20_cagr")),
            "friction_mdd": _safe_float(research_models.get("defensive_hold", {}).get("cost20_mdd")),
            "friction_sharpe": _safe_float(research_models.get("defensive_hold", {}).get("cost20_sharpe")),
        },
        {
            "label": str(operating_index.get("attack_challenger_candidate") or "attack_challenger"),
            "role": "attack_challenger",
            "source": "operating_index",
            "cagr": _safe_float(operating_index.get("attack_challenger_paper_validation_cagr")),
            "mdd": _safe_float(operating_index.get("attack_challenger_paper_validation_max_drawdown")),
            "sharpe": None,
            "oos_cagr": None,
            "oos_mdd": None,
            "oos_sharpe": None,
            "drift": _safe_float(operating_index.get("attack_challenger_walk_forward_sensitivity_max_drift")) or 0.0,
            "friction_cagr": None,
            "friction_mdd": None,
            "friction_sharpe": None,
        },
    ]
    candidates = [row for row in candidates if row["label"] not in {"", "None"} and row.get("cagr") is not None and row.get("mdd") is not None]

    attack_pool = [row for row in candidates if row["role"] in {"attack_main", "attack_backup", "attack_challenger"}]
    operating_pool = [row for row in candidates if row["role"] in {"operating_practical", "defensive_hold"}]

    for row in attack_pool:
        row["selection_score"] = round(_score_attack(row), 8)
    for row in operating_pool:
        row["selection_score"] = round(_score_operating(row), 8)

    attack_selected = max(attack_pool, key=lambda row: float(row["selection_score"]))
    operating_selected = max(operating_pool, key=lambda row: float(row["selection_score"]))

    return {
        "generated_at_utc": datetime.now(tz=UTC).isoformat(),
        "objective_map": {
            "attack": "maximize_cagr",
            "operating": "minimize_mdd",
        },
        "attack_model": {
            **attack_selected,
            "selection_reason": "Highest attack score from current attack pool.",
        },
        "operating_model": {
            **operating_selected,
            "selection_reason": "Highest operating score from current defensive/practical pool.",
        },
        "attack_pool": attack_pool,
        "operating_pool": operating_pool,
        "reads": {
            "attack": _candidate_read(attack_selected),
            "operating": _candidate_read(operating_selected),
        },
        "source_paths": {
            "practical_scorecard": str(analysis_dir / "btc_1d_practical_scorecard_latest.json"),
            "research_stack_operating_brief": str(analysis_dir / "btc_1d_research_stack_operating_brief_latest.json"),
            "operating_index": str(analysis_dir / "btc_1d_operating_index_latest.json"),
        },
    }


def render_text(payload: dict[str, Any]) -> str:
    attack = payload["attack_model"]
    operating = payload["operating_model"]
    lines = [
        f"attack_model: {attack['label']}",
        f"attack_read: {_candidate_read(attack)}",
        f"attack_reason: {attack['selection_reason']}",
        "",
        f"operating_model: {operating['label']}",
        f"operating_read: {_candidate_read(operating)}",
        f"operating_reason: {operating['selection_reason']}",
    ]
    return "\n".join(lines)


def write_outputs(payload: dict[str, Any], *, output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = _utc_timestamp()
    json_path = output_dir / f"btc_1d_model_profile_selection_{stamp}.json"
    txt_path = output_dir / f"btc_1d_model_profile_selection_{stamp}.txt"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    txt_path.write_text(render_text(payload) + "\n", encoding="utf-8")

    latest_json = output_dir / "btc_1d_model_profile_selection_latest.json"
    latest_txt = output_dir / "btc_1d_model_profile_selection_latest.txt"
    latest_json.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
    latest_txt.write_text(txt_path.read_text(encoding="utf-8"), encoding="utf-8")
    return {
        "json": str(json_path),
        "txt": str(txt_path),
        "latest_json": str(latest_json),
        "latest_txt": str(latest_txt),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Select the current BTC 1d attack and operating model leaders.")
    parser.add_argument("--analysis-dir", type=Path, default=Path("analysis_results"))
    parser.add_argument("--write-output", action="store_true")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    payload = build_model_profile_selection(analysis_dir=args.analysis_dir)
    if args.write_output:
        payload["artifacts"] = write_outputs(payload, output_dir=args.analysis_dir)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_text(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
