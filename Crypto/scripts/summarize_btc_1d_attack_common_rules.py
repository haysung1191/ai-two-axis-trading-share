from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from statistics import median
from typing import Any


@dataclass(frozen=True)
class AttackArtifact:
    family: str
    path: Path


DEFAULT_ARTIFACTS: tuple[AttackArtifact, ...] = (
    AttackArtifact("brief_close_above_reset_continuation", Path("analysis_results/btc_1d_brief_close_above_reset_continuation_high_cagr_batch_20260415T202058Z.json")),
    AttackArtifact("brief_inside_day_reset_continuation", Path("analysis_results/btc_1d_brief_inside_day_reset_continuation_high_cagr_batch_20260415T203156Z.json")),
    AttackArtifact("volatility_expansion_pullthrough", Path("analysis_results/btc_1d_volatility_expansion_pullthrough_high_cagr_batch_20260415T174435Z.json")),
    AttackArtifact("volatility_spike_reversal_continuation", Path("analysis_results/btc_1d_volatility_spike_reversal_continuation_high_cagr_batch_20260415T171339Z.json")),
    AttackArtifact("post_spike_consolidation_breakout", Path("analysis_results/btc_1d_post_spike_consolidation_breakout_high_cagr_batch_20260415T170649Z.json")),
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _pick_family_leader(results: list[dict[str, Any]]) -> dict[str, Any] | None:
    eligible = []
    for row in results:
        if not isinstance(row, dict):
            continue
        cagr = _safe_float(row.get("cagr"))
        mdd = _safe_float(row.get("max_drawdown"))
        sharpe = _safe_float(row.get("sharpe"))
        if cagr is None or mdd is None or sharpe is None:
            continue
        if cagr < 0.20:
            continue
        eligible.append(row)
    if not eligible:
        return None
    return max(eligible, key=lambda row: (float(row["cagr"]), -float(row["max_drawdown"]), float(row["sharpe"])))


def _summarize_parameter_ranges(leaders: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    param_values: dict[str, list[float]] = {}
    for leader in leaders:
        parameters = leader.get("parameters", {})
        if not isinstance(parameters, dict):
            continue
        for key, value in parameters.items():
            numeric_value = _safe_float(value)
            if numeric_value is None:
                continue
            param_values.setdefault(str(key), []).append(numeric_value)

    summary: dict[str, dict[str, float]] = {}
    minimum_presence = max(2, int(len(leaders) * 0.6))
    for key, values in sorted(param_values.items()):
        if len(values) < minimum_presence:
            continue
        summary[key] = {
            "min": round(min(values), 6),
            "median": round(float(median(values)), 6),
            "max": round(max(values), 6),
            "count": float(len(values)),
        }
    return summary


def build_attack_common_rules(*, artifacts: tuple[AttackArtifact, ...] = DEFAULT_ARTIFACTS) -> dict[str, Any]:
    family_rows: list[dict[str, Any]] = []
    leaders: list[dict[str, Any]] = []

    for artifact in artifacts:
        payload = _load_json(artifact.path)
        results = payload.get("results", [])
        if not isinstance(results, list):
            continue
        leader = _pick_family_leader(results)
        row = {
            "family": artifact.family,
            "artifact_path": str(artifact.path),
            "leader_found": leader is not None,
        }
        if leader is not None:
            enriched_leader = {
                "family": artifact.family,
                "strategy_name": str(leader.get("strategy_name") or ""),
                "variant_label": str(leader.get("variant_label") or ""),
                "decision": str(leader.get("decision") or ""),
                "cagr": float(leader["cagr"]),
                "max_drawdown": float(leader["max_drawdown"]),
                "sharpe": float(leader["sharpe"]),
                "trades": int(leader.get("trades") or 0),
                "completed_trades": int(leader.get("completed_trades") or 0),
                "parameters": dict(leader.get("parameters") or {}),
            }
            row.update(
                {
                    "strategy_name": enriched_leader["strategy_name"],
                    "variant_label": enriched_leader["variant_label"],
                    "cagr": enriched_leader["cagr"],
                    "max_drawdown": enriched_leader["max_drawdown"],
                    "sharpe": enriched_leader["sharpe"],
                }
            )
            leaders.append(enriched_leader)
        family_rows.append(row)

    leaders.sort(key=lambda row: (-row["cagr"], row["max_drawdown"], -row["sharpe"]))
    parameter_ranges = _summarize_parameter_ranges(leaders)

    priority_hints = []
    if "min_atr_expansion_ratio" in parameter_ranges:
        band = parameter_ranges["min_atr_expansion_ratio"]
        priority_hints.append(
            f"Prefer ATR expansion ratio around {band['median']:.2f} with observed band {band['min']:.2f}-{band['max']:.2f}."
        )
    if "trend_ema_window" in parameter_ranges:
        band = parameter_ranges["trend_ema_window"]
        priority_hints.append(
            f"Keep trend EMA window in the {band['min']:.0f}-{band['max']:.0f} zone; median leader uses {band['median']:.0f}."
        )
    if "max_hold_bars" in parameter_ranges:
        band = parameter_ranges["max_hold_bars"]
        priority_hints.append(
            f"Attack leaders cluster around hold horizon {band['median']:.0f} bars with band {band['min']:.0f}-{band['max']:.0f}."
        )
    if "min_volume_ratio" in parameter_ranges:
        band = parameter_ranges["min_volume_ratio"]
        priority_hints.append(
            f"Require volume confirmation roughly above {band['median']:.2f}; weaker sub-{band['min']:.2f} settings have not led the current attack set."
        )

    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    return {
        "generated_at": stamp,
        "leader_count": len(leaders),
        "families": family_rows,
        "leaders": leaders,
        "parameter_ranges": parameter_ranges,
        "priority_hints": priority_hints,
        "recommended_attack_rule_seed": {
            key: value["median"] for key, value in parameter_ranges.items()
        },
    }


def _render_text(payload: dict[str, Any]) -> str:
    lines = [
        f"leader_count: {payload.get('leader_count', 0)}",
        "leaders:",
    ]
    for row in payload.get("leaders", []):
        lines.append(
            f"  - {row['family']} | {row['variant_label']} | cagr={row['cagr']:.4f} | mdd={row['max_drawdown']:.4f} | sharpe={row['sharpe']:.4f}"
        )
    if payload.get("priority_hints"):
        lines.append("")
        lines.append("priority_hints:")
        for hint in payload["priority_hints"]:
            lines.append(f"  - {hint}")
    return "\n".join(lines)


def write_outputs(payload: dict[str, Any], *, analysis_dir: Path) -> dict[str, str]:
    analysis_dir.mkdir(parents=True, exist_ok=True)
    stamp = payload["generated_at"]
    json_path = analysis_dir / f"btc_1d_attack_common_rules_{stamp}.json"
    txt_path = analysis_dir / f"btc_1d_attack_common_rules_{stamp}.txt"
    latest_json = analysis_dir / "btc_1d_attack_common_rules_latest.json"
    latest_txt = analysis_dir / "btc_1d_attack_common_rules_latest.txt"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    txt_path.write_text(_render_text(payload) + "\n", encoding="utf-8")
    latest_json.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
    latest_txt.write_text(txt_path.read_text(encoding="utf-8"), encoding="utf-8")
    return {
        "json": str(json_path),
        "txt": str(txt_path),
        "latest_json": str(latest_json),
        "latest_txt": str(latest_txt),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize common rules across current BTC 1d attack leaders.")
    parser.add_argument("--analysis-dir", type=Path, default=Path("analysis_results"))
    parser.add_argument("--write-output", action="store_true")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    payload = build_attack_common_rules()
    if args.write_output:
        payload["artifacts"] = write_outputs(payload, analysis_dir=args.analysis_dir)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(_render_text(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
