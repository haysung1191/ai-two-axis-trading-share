from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.domains.experiments.btc_paper_validation import BtcPaperValidationService
from app.domains.experiments.btc_1d_volatility_spike_reversal_continuation_exit_compression_batch import (
    Btc1dVolatilitySpikeReversalContinuationExitCompressionBatchService,
    Btc1dVolatilitySpikeReversalContinuationExitCompressionConfig,
)
from scripts.validate_btc_1d_volatility_spike_reversal_continuation_tightstop_candidate import (
    parse_args as parse_candidate_args,
)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the BTC 1d secondary repair step.")
    parser.add_argument("--analysis-dir", type=Path, default=Path("analysis_results"))
    parser.add_argument("--periods", type=int, default=2200)
    parser.add_argument("--fee-bps", type=float, default=8.0)
    parser.add_argument("--slippage-bps", type=float, default=8.0)
    parser.add_argument("--step", choices=["candidate_repair_retest", "candidate_parameter_repair"], default="candidate_repair_retest")
    parser.add_argument("--allow-synthetic-ohlcv-fallback", action="store_true")
    return parser


def build_secondary_repair_step_report(*, step: str, validation_result: dict) -> dict:
    resolved_payload = validation_result
    if "config" not in resolved_payload and validation_result.get("analysis_result_json"):
        resolved_payload = _load_json(ROOT / str(validation_result["analysis_result_json"]))

    decision = resolved_payload["decision_record"]
    metrics = decision["key_metrics"]
    failed_gates = list(decision["failed_gates"])
    clears_drawdown_gate = "backtest_max_drawdown" not in failed_gates

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "step": step,
        "candidate": {
            "label": "volatility_spike_reversal_continuation_tighter_stop",
            "strategy_name": resolved_payload["config"]["strategy_name"],
            "decision": decision["decision"],
            "failed_gates": failed_gates,
            "cagr": float(metrics["cagr"]),
            "max_drawdown": float(metrics["max_drawdown"]),
            "sharpe": float(metrics["sharpe"]),
            "win_rate": float(metrics["win_rate"]),
            "completed_trades": float(metrics["completed_trades"]),
        },
        "validation_result_ref": {
            "run_id": validation_result["run_id"],
            "analysis_result_json": validation_result["analysis_result_json"],
        },
        "repair_gate_check": {
            "clears_drawdown_gate": clears_drawdown_gate,
            "keeps_min_cagr": float(metrics["cagr"]) >= 0.25,
            "keeps_min_sharpe": float(metrics["sharpe"]) >= 1.0,
        },
    }
    report["step_verdict"] = {
        "status": "advance_to_friction_retest" if clears_drawdown_gate else "stay_in_candidate_repair_loop",
        "next_step": "friction_retest" if clears_drawdown_gate else "candidate_parameter_repair",
        "reason": (
            "The candidate retest cleared the drawdown blocker, so the next step is friction retest."
            if clears_drawdown_gate
            else "The candidate retest still fails the drawdown gate, so the next step stays inside candidate parameter repair."
        ),
    }
    return report


def build_secondary_parameter_repair_report(*, step: str, batch_result: dict) -> dict:
    current_variant = next(row for row in batch_result["results"] if row["variant_label"] == "tighter_stop")
    best_variant = min(
        batch_result["results"],
        key=lambda row: (float(row["max_drawdown"]), -float(row["cagr"]), -float(row["sharpe"])),
    )
    improves_drawdown = float(best_variant["max_drawdown"]) < float(current_variant["max_drawdown"])

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "step": step,
        "current_candidate_variant": {
            "variant_label": current_variant["variant_label"],
            "strategy_name": current_variant["strategy_name"],
            "cagr": float(current_variant["cagr"]),
            "max_drawdown": float(current_variant["max_drawdown"]),
            "sharpe": float(current_variant["sharpe"]),
            "failed_gates": list(current_variant["failed_gates"]),
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
            "failed_gates": list(best_variant["failed_gates"]),
        },
        "repair_gate_check": {
            "improves_drawdown_vs_current": improves_drawdown,
            "keeps_min_cagr": float(best_variant["cagr"]) >= 0.25,
            "keeps_min_sharpe": float(best_variant["sharpe"]) >= 1.0,
        },
    }
    report["step_verdict"] = {
        "status": "advance_to_friction_retest"
        if report["repair_gate_check"]["improves_drawdown_vs_current"]
        and report["repair_gate_check"]["keeps_min_cagr"]
        and report["repair_gate_check"]["keeps_min_sharpe"]
        else "secondary_repair_exhausted",
        "next_step": "friction_retest"
        if report["repair_gate_check"]["improves_drawdown_vs_current"]
        and report["repair_gate_check"]["keeps_min_cagr"]
        and report["repair_gate_check"]["keeps_min_sharpe"]
        else "new_family_search_or_secondary_reframe",
        "reason": (
            "Parameter repair found a better drawdown shape without breaking the basic attack profile, so the next step is friction retest."
            if report["repair_gate_check"]["improves_drawdown_vs_current"]
            and report["repair_gate_check"]["keeps_min_cagr"]
            and report["repair_gate_check"]["keeps_min_sharpe"]
            else "Parameter repair did not find a drawdown-improving variant over the current tighter-stop candidate, so this secondary repair loop is exhausted."
        ),
    }
    return report


def run_candidate_repair_step(args: argparse.Namespace) -> dict:
    cfg = parse_candidate_args(
        [
            "--periods",
            str(args.periods),
            "--fee-bps",
            str(args.fee_bps),
            "--slippage-bps",
            str(args.slippage_bps),
            *(["--allow-synthetic-ohlcv-fallback"] if args.allow_synthetic_ohlcv_fallback else []),
        ]
    )
    validation_result = BtcPaperValidationService(analysis_results_dir=args.analysis_dir).run_validation(cfg)
    return build_secondary_repair_step_report(
        step="candidate_repair_retest",
        validation_result=validation_result,
    )


def run_candidate_parameter_repair_step(args: argparse.Namespace) -> dict:
    config = Btc1dVolatilitySpikeReversalContinuationExitCompressionConfig(
        periods=args.periods,
        fee_bps=args.fee_bps,
        slippage_bps=args.slippage_bps,
        allow_synthetic_ohlcv_fallback=bool(args.allow_synthetic_ohlcv_fallback),
    )
    batch_result = Btc1dVolatilitySpikeReversalContinuationExitCompressionBatchService(
        analysis_results_dir=args.analysis_dir
    ).run_batch(config)
    return build_secondary_parameter_repair_report(
        step="candidate_parameter_repair",
        batch_result=batch_result,
    )


def _render_markdown(report: dict) -> str:
    if report["step"] == "candidate_parameter_repair":
        current = report["current_candidate_variant"]
        best = report["best_variant"]
        gate = report["repair_gate_check"]
        verdict = report["step_verdict"]
        return "\n".join(
            [
                "# BTC 1d Secondary Repair Step",
                "",
                f"- Step: `{report['step']}`",
                f"- Current candidate variant: `{current['variant_label']}` | `{current['cagr']:.4f}` CAGR / `{current['max_drawdown']:.4f}` MDD / Sharpe `{current['sharpe']:.4f}`",
                f"- Best repair variant: `{best['variant_label']}` | `{best['cagr']:.4f}` CAGR / `{best['max_drawdown']:.4f}` MDD / Sharpe `{best['sharpe']:.4f}`",
                f"- Improves drawdown vs current: `{gate['improves_drawdown_vs_current']}`",
                f"- Keeps min CAGR: `{gate['keeps_min_cagr']}`",
                f"- Keeps min Sharpe: `{gate['keeps_min_sharpe']}`",
                f"- Step verdict: `{verdict['status']}`",
                f"- Next step: `{verdict['next_step']}`",
                f"- Reason: {verdict['reason']}",
                "",
            ]
        )

    candidate = report["candidate"]
    gate = report["repair_gate_check"]
    verdict = report["step_verdict"]
    return "\n".join(
        [
            "# BTC 1d Secondary Repair Step",
            "",
            f"- Step: `{report['step']}`",
            f"- Candidate: `{candidate['label']}`",
            f"- Decision: `{candidate['decision']}`",
            f"- Base: `{candidate['cagr']:.4f}` CAGR / `{candidate['max_drawdown']:.4f}` MDD / Sharpe `{candidate['sharpe']:.4f}`",
            f"- Failed gates: `{', '.join(candidate['failed_gates']) if candidate['failed_gates'] else '-'}`",
            f"- Clears drawdown gate: `{gate['clears_drawdown_gate']}`",
            f"- Keeps min CAGR: `{gate['keeps_min_cagr']}`",
            f"- Keeps min Sharpe: `{gate['keeps_min_sharpe']}`",
            f"- Step verdict: `{verdict['status']}`",
            f"- Next step: `{verdict['next_step']}`",
            f"- Reason: {verdict['reason']}",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.step == "candidate_repair_retest":
        report = run_candidate_repair_step(args)
    elif args.step == "candidate_parameter_repair":
        report = run_candidate_parameter_repair_step(args)
    else:
        raise ValueError(f"Unsupported step: {args.step}")
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = args.analysis_dir / f"btc_1d_secondary_repair_step_{stamp}.json"
    md_path = args.analysis_dir / f"btc_1d_secondary_repair_step_{stamp}.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    print(
        json.dumps(
            {
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "report": report,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
