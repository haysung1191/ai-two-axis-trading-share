from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.domains.experiments.btc_1d_trend_dip_reversal_breakout_exit_compression_batch import (
    Btc1dTrendDipReversalBreakoutExitCompressionBatchService,
    Btc1dTrendDipReversalBreakoutExitCompressionConfig,
    DEFAULT_VARIANTS as EXIT_COMPRESSION_DEFAULT_VARIANTS,
    build_seed_aligned_variants,
)
from app.domains.experiments.btc_1d_trend_dip_reversal_breakout_exit_symmetry_batch import (
    Btc1dTrendDipReversalBreakoutExitSymmetryBatchService,
    Btc1dTrendDipReversalBreakoutExitSymmetryConfig,
)
from scripts.compare_btc_1d_trend_dip_attack_reopen_screen import (
    build_report as build_trend_dip_reopen_screen,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the BTC 1d attack primary queue step.")
    parser.add_argument("--analysis-dir", type=Path, default=Path("analysis_results"))
    parser.add_argument("--periods", type=int, default=2200)
    parser.add_argument("--fee-bps", type=float, default=8.0)
    parser.add_argument("--slippage-bps", type=float, default=8.0)
    parser.add_argument("--step", choices=["exit_compression_batch", "exit_symmetry_batch"], default="exit_compression_batch")
    parser.add_argument("--allow-synthetic-ohlcv-fallback", action="store_true")
    parser.add_argument("--apply-attack-seed", action="store_true")
    return parser


def _load_attack_rule_seed(analysis_dir: Path) -> dict:
    path = analysis_dir / "btc_1d_attack_common_rules_latest.json"
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return dict(payload.get("recommended_attack_rule_seed", {}) or {})


def _select_best_by_mdd(rows: list[dict]) -> dict:
    return min(rows, key=lambda row: (float(row["max_drawdown"]), -float(row["cagr"]), -float(row["sharpe"])))


def build_primary_step_report(*, step: str, batch_result: dict, anchor_report: dict) -> dict:
    anchor = anchor_report["current_candidate"]
    best_variant = _select_best_by_mdd(batch_result["results"])
    mdd_delta = float(best_variant["max_drawdown"]) - float(anchor["max_drawdown"])
    cagr_delta = float(best_variant["cagr"]) - float(anchor["cagr"])

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "step": step,
        "current_anchor": {
            "label": anchor["label"],
            "strategy_name": anchor["strategy_name"],
            "cagr": float(anchor["cagr"]),
            "max_drawdown": float(anchor["max_drawdown"]),
            "sharpe": float(anchor["sharpe"]),
        },
        "batch_result_ref": {
            "run_id": batch_result["run_id"],
            "analysis_result_json": batch_result["analysis_result_json"],
            "analysis_result_csv": batch_result["analysis_result_csv"],
        },
        "best_variant": {
            "variant_label": best_variant["variant_label"],
            "strategy_name": best_variant["strategy_name"],
            "cagr": float(best_variant["cagr"]),
            "max_drawdown": float(best_variant["max_drawdown"]),
            "sharpe": float(best_variant["sharpe"]),
            "completed_trades": int(best_variant["completed_trades"]),
            "failed_gates": list(best_variant["failed_gates"]),
        },
        "comparison": {
            "mdd_delta_vs_anchor": mdd_delta,
            "cagr_delta_vs_anchor": cagr_delta,
            "improves_drawdown": mdd_delta < 0.0,
            "keeps_attack_profile": float(best_variant["cagr"]) >= float(anchor["cagr"]) * 0.95,
        },
    }
    report["step_verdict"] = {
        "status": (
            "advance_to_candidate_validation"
            if report["comparison"]["improves_drawdown"] and report["comparison"]["keeps_attack_profile"]
            else "stay_in_primary_mutation_loop"
        ),
        "next_step": (
            "candidate_validation"
            if report["comparison"]["improves_drawdown"] and report["comparison"]["keeps_attack_profile"]
            else ("exit_symmetry_batch" if step == "exit_compression_batch" else "hold_primary_anchor")
        ),
        "reason": (
            "Exit compression beat the current drawdown anchor without breaking the attack profile enough to justify candidate validation."
            if report["comparison"]["improves_drawdown"] and report["comparison"]["keeps_attack_profile"]
            else (
                "Exit compression still does not clear the drawdown-and-profile gate, so the next queue step stays in mutation space."
                if step == "exit_compression_batch"
                else "Exit symmetry also failed to beat the current drawdown anchor, so the primary lane should hold the current anchor and stop mutation expansion here."
            )
        ),
    }
    return report


def _render_markdown(report: dict) -> str:
    anchor = report["current_anchor"]
    best = report["best_variant"]
    comparison = report["comparison"]
    verdict = report["step_verdict"]
    return "\n".join(
        [
            "# BTC 1d Attack Primary Queue Step",
            "",
            f"- Step: `{report['step']}`",
            f"- Current anchor: `{anchor['label']}` | `{anchor['cagr']:.4f}` CAGR / `{anchor['max_drawdown']:.4f}` MDD / Sharpe `{anchor['sharpe']:.4f}`",
            f"- Best variant: `{best['variant_label']}` | `{best['cagr']:.4f}` CAGR / `{best['max_drawdown']:.4f}` MDD / Sharpe `{best['sharpe']:.4f}`",
            f"- MDD delta vs anchor: `{comparison['mdd_delta_vs_anchor']:.4f}`",
            f"- CAGR delta vs anchor: `{comparison['cagr_delta_vs_anchor']:.4f}`",
            f"- Improves drawdown: `{comparison['improves_drawdown']}`",
            f"- Keeps attack profile: `{comparison['keeps_attack_profile']}`",
            f"- Step verdict: `{verdict['status']}`",
            f"- Next step: `{verdict['next_step']}`",
            f"- Reason: {verdict['reason']}",
            "",
        ]
    )


def run_exit_compression_step(args: argparse.Namespace) -> dict:
    config = Btc1dTrendDipReversalBreakoutExitCompressionConfig(
        periods=args.periods,
        fee_bps=args.fee_bps,
        slippage_bps=args.slippage_bps,
        allow_synthetic_ohlcv_fallback=bool(args.allow_synthetic_ohlcv_fallback),
    )
    seed_parameters = _load_attack_rule_seed(args.analysis_dir) if bool(args.apply_attack_seed) else {}
    variants = build_seed_aligned_variants(
        seed_parameters,
        base_variants=EXIT_COMPRESSION_DEFAULT_VARIANTS,
    )
    batch_result = Btc1dTrendDipReversalBreakoutExitCompressionBatchService(
        analysis_results_dir=args.analysis_dir
    ).run_batch(config, variants=variants)
    anchor_report = build_trend_dip_reopen_screen()
    report = build_primary_step_report(
        step="exit_compression_batch",
        batch_result=batch_result,
        anchor_report=anchor_report,
    )
    report["seed_application"] = {
        "attack_seed_applied": bool(args.apply_attack_seed),
        "attack_seed_parameters": seed_parameters,
        "variant_count": len(variants),
    }
    return report


def run_exit_symmetry_step(args: argparse.Namespace) -> dict:
    config = Btc1dTrendDipReversalBreakoutExitSymmetryConfig(
        periods=args.periods,
        fee_bps=args.fee_bps,
        slippage_bps=args.slippage_bps,
        allow_synthetic_ohlcv_fallback=bool(args.allow_synthetic_ohlcv_fallback),
    )
    batch_result = Btc1dTrendDipReversalBreakoutExitSymmetryBatchService(
        analysis_results_dir=args.analysis_dir
    ).run_batch(config)
    anchor_report = build_trend_dip_reopen_screen()
    report = build_primary_step_report(
        step="exit_symmetry_batch",
        batch_result=batch_result,
        anchor_report=anchor_report,
    )
    report["seed_application"] = {
        "attack_seed_applied": False,
        "attack_seed_parameters": {},
        "variant_count": len(batch_result["results"]),
    }
    return report


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.step == "exit_compression_batch":
        report = run_exit_compression_step(args)
    elif args.step == "exit_symmetry_batch":
        report = run_exit_symmetry_step(args)
    else:
        raise ValueError(f"Unsupported step: {args.step}")
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = args.analysis_dir / f"btc_1d_attack_primary_queue_step_{stamp}.json"
    md_path = args.analysis_dir / f"btc_1d_attack_primary_queue_step_{stamp}.md"
    latest_json = args.analysis_dir / "btc_1d_attack_primary_queue_step_latest.json"
    latest_md = args.analysis_dir / "btc_1d_attack_primary_queue_step_latest.md"
    json_payload = json.dumps(report, indent=2)
    md_payload = _render_markdown(report)
    json_path.write_text(json_payload, encoding="utf-8")
    md_path.write_text(md_payload, encoding="utf-8")
    latest_json.write_text(json_payload, encoding="utf-8")
    latest_md.write_text(md_payload, encoding="utf-8")
    print(
        json.dumps(
            {
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "latest_json_path": str(latest_json),
                "latest_md_path": str(latest_md),
                "report": report,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
