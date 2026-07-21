from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RecentArtifact:
    family: str
    artifact_path: Path


DEFAULT_ARTIFACTS: tuple[RecentArtifact, ...] = (
    RecentArtifact("failed_breakout_continuation", Path("analysis_results/btc_1d_failed_breakout_continuation_high_cagr_batch_20260415T173844Z.json")),
    RecentArtifact("volatility_expansion_pullthrough", Path("analysis_results/btc_1d_volatility_expansion_pullthrough_high_cagr_batch_20260415T174435Z.json")),
    RecentArtifact("failed_downside_expansion_escape", Path("analysis_results/btc_1d_failed_downside_expansion_escape_high_cagr_batch_20260415T174939Z.json")),
    RecentArtifact("shallow_pullback_impulse_continuation", Path("analysis_results/btc_1d_shallow_pullback_impulse_continuation_high_cagr_batch_20260415T175459Z.json")),
    RecentArtifact("trend_dip_reversal_breakout", Path("analysis_results/btc_1d_trend_dip_reversal_breakout_high_cagr_batch_20260415T181947Z.json")),
    RecentArtifact("range_reclaim_acceleration", Path("analysis_results/btc_1d_range_reclaim_acceleration_high_cagr_batch_20260415T182946Z.json")),
    RecentArtifact("expansion_failure_recovery", Path("analysis_results/btc_1d_expansion_failure_recovery_high_cagr_batch_20260415T183450Z.json")),
    RecentArtifact("shallow_inside_compression_continuation", Path("analysis_results/btc_1d_shallow_inside_compression_continuation_high_cagr_batch_20260415T183956Z.json")),
    RecentArtifact("breakout_retest_acceleration", Path("analysis_results/btc_1d_breakout_retest_acceleration_high_cagr_batch_20260415T184525Z.json")),
    RecentArtifact("higher_low_squeeze_release", Path("analysis_results/btc_1d_higher_low_squeeze_release_high_cagr_batch_20260415T185030Z.json")),
    RecentArtifact("failed_retest_acceleration", Path("analysis_results/btc_1d_failed_retest_acceleration_high_cagr_batch_20260415T185553Z.json")),
    RecentArtifact("base_flip_breakout", Path("analysis_results/btc_1d_base_flip_breakout_high_cagr_batch_20260415T190120Z.json")),
    RecentArtifact("post_failure_range_expansion_reversal_confirmation", Path("analysis_results/btc_1d_post_failure_range_expansion_reversal_confirmation_high_cagr_batch_20260415T191300Z.json")),
    RecentArtifact("momentum_burst_shallow_reclaim_base", Path("analysis_results/btc_1d_momentum_burst_shallow_reclaim_base_high_cagr_batch_20260415T191719Z.json")),
    RecentArtifact("failed_inside_reset_ignition", Path("analysis_results/btc_1d_failed_inside_reset_ignition_high_cagr_batch_20260415T192230Z.json")),
    RecentArtifact("post_expansion_shelf_breakout", Path("analysis_results/btc_1d_post_expansion_shelf_breakout_high_cagr_batch_20260415T192757Z.json")),
    RecentArtifact("failed_pullthrough_fast_reclaim", Path("analysis_results/btc_1d_failed_pullthrough_fast_reclaim_high_cagr_batch_20260415T193313Z.json")),
    RecentArtifact("micro_undercut_reclaim_continuation", Path("analysis_results/btc_1d_micro_undercut_reclaim_continuation_high_cagr_batch_20260415T193825Z.json")),
    RecentArtifact("failed_base_expansion_continuation", Path("analysis_results/btc_1d_failed_base_expansion_continuation_high_cagr_batch_20260415T194338Z.json")),
    RecentArtifact("reclaim_shelf_acceleration", Path("analysis_results/btc_1d_reclaim_shelf_acceleration_high_cagr_batch_20260415T194848Z.json")),
    RecentArtifact("shallow_trap_reversal_acceleration", Path("analysis_results/btc_1d_shallow_trap_reversal_acceleration_high_cagr_batch_20260415T195620Z.json")),
    RecentArtifact("shallow_liquidity_void_refill_continuation", Path("analysis_results/btc_1d_shallow_liquidity_void_refill_continuation_high_cagr_batch_20260415T200015Z.json")),
    RecentArtifact("upside_imbalance_reclaim_continuation", Path("analysis_results/btc_1d_upside_imbalance_reclaim_continuation_high_cagr_batch_20260415T200540Z.json")),
    RecentArtifact("shallow_breakout_shelf_continuation", Path("analysis_results/btc_1d_shallow_breakout_shelf_continuation_high_cagr_batch_20260415T201030Z.json")),
    RecentArtifact("shallow_liquidity_grab_reclaim_continuation", Path("analysis_results/btc_1d_shallow_liquidity_grab_reclaim_continuation_high_cagr_batch_20260415T201553Z.json")),
    RecentArtifact("brief_close_above_reset_continuation", Path("analysis_results/btc_1d_brief_close_above_reset_continuation_high_cagr_batch_20260415T202058Z.json")),
    RecentArtifact("one_bar_failed_dip_continuation", Path("analysis_results/btc_1d_one_bar_failed_dip_continuation_high_cagr_batch_20260415T202607Z.json")),
    RecentArtifact("brief_inside_day_reset_continuation", Path("analysis_results/btc_1d_brief_inside_day_reset_continuation_high_cagr_batch_20260415T203156Z.json")),
    RecentArtifact("shallow_two_bar_squeeze_continuation", Path("analysis_results/btc_1d_shallow_two_bar_squeeze_continuation_high_cagr_batch_20260415T203836Z.json")),
    RecentArtifact("shallow_outside_bar_reset_continuation", Path("analysis_results/btc_1d_shallow_outside_bar_reset_continuation_high_cagr_batch_20260415T205438Z.json")),
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _best_result(payload: dict[str, Any]) -> dict[str, Any]:
    results = payload.get("results", [])
    if not results:
        raise ValueError("results missing")
    return max(
        results,
        key=lambda item: (
            float(item.get("cagr", 0.0)),
            -float(item.get("max_drawdown", 1.0)),
            float(item.get("sharpe", 0.0)),
        ),
    )


def _pct(value: float) -> float:
    return round(value * 100.0, 2)


def _label(cagr: float, mdd: float, sharpe: float, trades: int) -> str:
    if cagr >= 0.35 and mdd <= 0.30:
        return "attack_near_miss_hold"
    if cagr >= 0.20 and mdd <= 0.20 and sharpe >= 1.0:
        return "defensive_hold_only"
    if trades == 0:
        return "zero_trade_kill"
    if cagr <= 0.0:
        return "negative_kill"
    return "low_alpha_kill"


def _pattern_bucket(family: str) -> str:
    parts = family.split("_")
    if "failed" in parts:
        return "failure_recovery"
    if "reclaim" in parts or "undercut" in parts or "grab" in parts:
        return "reclaim_grab"
    if "shelf" in parts or "squeeze" in parts or "inside" in parts:
        return "compression_reset"
    if "breakout" in parts or "continuation" in parts:
        return "breakout_continuation"
    if "expansion" in parts:
        return "expansion_followthrough"
    return "other"


def _render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# BTC 1d Recent Family Comparative Screen",
        "",
        f"- total_families: `{payload['summary']['total_families']}`",
        f"- attack_near_miss_holds: `{payload['summary']['attack_near_miss_holds']}`",
        f"- defensive_holds: `{payload['summary']['defensive_holds']}`",
        f"- low_alpha_or_kill: `{payload['summary']['low_alpha_or_kill']}`",
        "",
        "| family | bucket | best variant | CAGR | MDD | Sharpe | trades | label |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['family']} | {row['pattern_bucket']} | {row['variant_label']} | {row['cagr_pct']}% | {row['mdd_pct']}% | {row['sharpe']} | {row['trades']} | {row['screen_label']} |"
        )
    lines.extend(
        [
            "",
            "## Pattern Summary",
        ]
    )
    for bucket, info in payload["pattern_summary"].items():
        lines.append(f"- {bucket}: count `{info['count']}`, best `{info['best_family']}`, label mix `{info['label_mix']}`")
    return "\n".join(lines) + "\n"


def build_recent_family_screen(
    *,
    analysis_results_dir: Path = Path("analysis_results"),
    artifacts: tuple[RecentArtifact, ...] = DEFAULT_ARTIFACTS,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []

    for artifact in artifacts:
        payload = _load_json(artifact.artifact_path)
        best = _best_result(payload)
        cagr = float(best["cagr"])
        mdd = float(best["max_drawdown"])
        sharpe = round(float(best["sharpe"]), 4)
        trades = int(best["trades"])
        row = {
            "family": artifact.family,
            "artifact_path": str(artifact.artifact_path),
            "variant_label": best["variant_label"],
            "strategy_name": best["strategy_name"],
            "decision": best["decision"],
            "cagr": cagr,
            "max_drawdown": mdd,
            "sharpe": sharpe,
            "trades": trades,
            "completed_trades": int(best["completed_trades"]),
            "pattern_bucket": _pattern_bucket(artifact.family),
            "screen_label": _label(cagr, mdd, sharpe, trades),
        }
        row["cagr_pct"] = _pct(cagr)
        row["mdd_pct"] = _pct(mdd)
        rows.append(row)

    rows.sort(key=lambda item: (-item["cagr"], item["max_drawdown"], -item["sharpe"]))

    pattern_summary: dict[str, dict[str, Any]] = {}
    for row in rows:
        bucket = row["pattern_bucket"]
        info = pattern_summary.setdefault(bucket, {"count": 0, "best_family": row["family"], "best_cagr": row["cagr"], "label_counts": {}})
        info["count"] += 1
        if row["cagr"] > info["best_cagr"]:
            info["best_cagr"] = row["cagr"]
            info["best_family"] = row["family"]
        info["label_counts"][row["screen_label"]] = info["label_counts"].get(row["screen_label"], 0) + 1

    normalized_pattern_summary: dict[str, dict[str, Any]] = {}
    for bucket, info in pattern_summary.items():
        normalized_pattern_summary[bucket] = {
            "count": info["count"],
            "best_family": info["best_family"],
            "best_cagr_pct": _pct(info["best_cagr"]),
            "label_mix": ", ".join(f"{label}:{count}" for label, count in sorted(info["label_counts"].items())),
        }

    summary = {
        "total_families": len(rows),
        "attack_near_miss_holds": sum(1 for row in rows if row["screen_label"] == "attack_near_miss_hold"),
        "defensive_holds": sum(1 for row in rows if row["screen_label"] == "defensive_hold_only"),
        "low_alpha_or_kill": sum(1 for row in rows if row["screen_label"] in {"low_alpha_kill", "negative_kill", "zero_trade_kill"}),
        "top_family": rows[0]["family"] if rows else "none",
        "top_family_cagr_pct": rows[0]["cagr_pct"] if rows else 0.0,
    }

    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    output_json = analysis_results_dir / f"btc_1d_recent_family_comparative_screen_{stamp}.json"
    output_md = analysis_results_dir / f"btc_1d_recent_family_comparative_screen_{stamp}.md"

    result = {
        "generated_at": stamp,
        "rows": rows,
        "pattern_summary": normalized_pattern_summary,
        "summary": summary,
        "analysis_result_json": str(output_json),
        "analysis_result_md": str(output_md),
    }

    analysis_results_dir.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(result, indent=2), encoding="utf-8")
    output_md.write_text(_render_markdown(result), encoding="utf-8")
    return result


def main() -> int:
    result = build_recent_family_screen()
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
