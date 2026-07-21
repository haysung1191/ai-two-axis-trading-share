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
from scripts.validate_btc_1d_shallow_liquidity_void_refill_candidate import (
    parse_args as parse_candidate_args,
)
from scripts.validate_btc_1d_shallow_liquidity_void_refill_friction import (
    _decision as friction_decision,
    _run_validation as run_friction_validation,
)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the BTC 1d shallow liquidity void refill repair step.")
    parser.add_argument("--analysis-dir", type=Path, default=Path("analysis_results"))
    parser.add_argument("--periods", type=int, default=2200)
    parser.add_argument("--fee-bps", type=float, default=8.0)
    parser.add_argument("--slippage-bps", type=float, default=8.0)
    parser.add_argument(
        "--step",
        choices=["candidate_repair_retest", "friction_retest"],
        default="candidate_repair_retest",
    )
    parser.add_argument("--cost-levels-bps", nargs="*", type=float, default=[0.0, 8.0, 12.0, 20.0])
    parser.add_argument("--allow-synthetic-ohlcv-fallback", action="store_true")
    return parser


def build_candidate_repair_report(*, step: str, validation_result: dict) -> dict:
    resolved_payload = validation_result
    if "config" not in resolved_payload and validation_result.get("analysis_result_json"):
        resolved_payload = _load_json(ROOT / str(validation_result["analysis_result_json"]))

    decision = resolved_payload["decision_record"]
    metrics = decision["key_metrics"]
    failed_gates = list(decision["failed_gates"])
    clears_sensitivity_gate = "overfitting_sensitivity" not in failed_gates
    clears_overfitting_pass = "overfitting_pass" not in failed_gates
    clears_overfitting_flags = "overfitting_flags" not in failed_gates

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "step": step,
        "candidate": {
            "label": "shallow_liquidity_void_refill_continuation_reference",
            "strategy_name": resolved_payload["config"]["strategy_name"],
            "decision": decision["decision"],
            "failed_gates": failed_gates,
            "cagr": float(metrics["cagr"]),
            "max_drawdown": float(metrics["max_drawdown"]),
            "sharpe": float(metrics["sharpe"]),
            "win_rate": float(metrics["win_rate"]),
            "completed_trades": float(metrics.get("completed_trades", metrics.get("trades", 0.0))),
        },
        "validation_result_ref": {
            "run_id": validation_result["run_id"],
            "analysis_result_json": validation_result["analysis_result_json"],
        },
        "repair_gate_check": {
            "clears_overfitting_sensitivity": clears_sensitivity_gate,
            "clears_overfitting_pass": clears_overfitting_pass,
            "clears_overfitting_flags": clears_overfitting_flags,
            "keeps_target_drawdown": float(metrics["max_drawdown"]) <= 0.18,
            "keeps_target_cagr": float(metrics["cagr"]) >= 0.22,
        },
    }
    ready_for_friction = (
        report["repair_gate_check"]["clears_overfitting_sensitivity"]
        and report["repair_gate_check"]["keeps_target_drawdown"]
        and report["repair_gate_check"]["keeps_target_cagr"]
    )
    report["step_verdict"] = {
        "status": "advance_to_friction_retest" if ready_for_friction else "stay_in_candidate_repair_loop",
        "next_step": "friction_retest" if ready_for_friction else "continue_candidate_repair_search",
        "reason": (
            "The candidate retest cleared the sensitivity blocker while keeping the target attack profile, so the next step is friction retest."
            if ready_for_friction
            else "The candidate retest still carries the overfitting sensitivity blocker or falls outside the target profile, so the lane stays inside candidate repair."
        ),
    }
    return report


def build_friction_repair_report(*, step: str, friction_result: dict) -> dict:
    levels = friction_result["levels"]
    baseline = min(levels, key=lambda row: float(row["cost_bps"]))
    clears_sensitivity_gate = "overfitting_sensitivity" not in baseline["failed_gates"]
    flips_pause = friction_result["final_decision"] != "pause"

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "step": step,
        "candidate": {
            "label": "shallow_liquidity_void_refill_continuation_reference",
            "final_decision": friction_result["final_decision"],
            "decision_reason": friction_result["decision_reason"],
        },
        "friction_result_ref": {
            "report_json_path": friction_result["report_json_path"],
            "report_md_path": friction_result["report_md_path"],
        },
        "baseline_level": {
            "cost_bps": float(baseline["cost_bps"]),
            "decision": baseline["decision"],
            "cagr": float(baseline["cagr"]),
            "max_drawdown": float(baseline["max_drawdown"]),
            "sharpe": float(baseline["sharpe"]),
            "failed_gates": list(baseline["failed_gates"]),
        },
        "repair_gate_check": {
            "flips_pause_decision": flips_pause,
            "clears_overfitting_sensitivity": clears_sensitivity_gate,
            "keeps_target_drawdown": float(baseline["max_drawdown"]) <= 0.18,
            "keeps_target_cagr": float(baseline["cagr"]) >= 0.22,
        },
    }
    ready_for_exit_batch = (
        report["repair_gate_check"]["flips_pause_decision"]
        and report["repair_gate_check"]["clears_overfitting_sensitivity"]
        and report["repair_gate_check"]["keeps_target_drawdown"]
        and report["repair_gate_check"]["keeps_target_cagr"]
    )
    report["step_verdict"] = {
        "status": "advance_to_exit_compression_retest" if ready_for_exit_batch else "stay_in_friction_repair_loop",
        "next_step": "exit_compression_retest" if ready_for_exit_batch else "continue_friction_repair_search",
        "reason": (
            "The friction retest flipped the lane away from pause and kept the repair targets intact, so the next step is exit compression retest."
            if ready_for_exit_batch
            else "The friction retest still leaves the lane paused or sensitivity-blocked, so the lane stays inside friction repair."
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
    return build_candidate_repair_report(
        step="candidate_repair_retest",
        validation_result=validation_result,
    )


def run_friction_repair_step(args: argparse.Namespace) -> dict:
    levels: list[dict] = []
    for cost_bps in args.cost_levels_bps:
        result = run_friction_validation(
            analysis_dir=args.analysis_dir,
            periods=args.periods,
            cost_bps=float(cost_bps),
            allow_synthetic_ohlcv_fallback=bool(args.allow_synthetic_ohlcv_fallback),
        )
        decision = result["decision_record"]
        metrics = decision["key_metrics"]
        levels.append(
            {
                "cost_bps": float(cost_bps),
                "decision": decision["decision"],
                "sharpe": float(metrics["sharpe"]),
                "cagr": float(metrics["cagr"]),
                "max_drawdown": float(metrics["max_drawdown"]),
                "win_rate": float(metrics["win_rate"]),
                "trades": float(metrics["trades"]),
                "failed_gates": list(decision["failed_gates"]),
                "analysis_result_json": result["analysis_result_json"],
            }
        )

    final_decision, reason = friction_decision(levels)
    friction_result = {
        "report_json_path": None,
        "report_md_path": None,
        "levels": levels,
        "final_decision": final_decision,
        "decision_reason": reason,
    }
    return build_friction_repair_report(step="friction_retest", friction_result=friction_result)


def _render_markdown(report: dict) -> str:
    if report["step"] == "friction_retest":
        baseline = report["baseline_level"]
        gate = report["repair_gate_check"]
        verdict = report["step_verdict"]
        return "\n".join(
            [
                "# BTC 1d Shallow Liquidity Void Refill Repair Step",
                "",
                f"- Step: `{report['step']}`",
                f"- Final decision: `{report['candidate']['final_decision']}`",
                f"- Baseline 0 bps: `{baseline['cagr']:.4f}` CAGR / `{baseline['max_drawdown']:.4f}` MDD / Sharpe `{baseline['sharpe']:.4f}`",
                f"- Baseline failed gates: `{', '.join(baseline['failed_gates']) if baseline['failed_gates'] else '-'}`",
                f"- Flips pause decision: `{gate['flips_pause_decision']}`",
                f"- Clears overfitting sensitivity: `{gate['clears_overfitting_sensitivity']}`",
                f"- Keeps target drawdown: `{gate['keeps_target_drawdown']}`",
                f"- Keeps target CAGR: `{gate['keeps_target_cagr']}`",
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
            "# BTC 1d Shallow Liquidity Void Refill Repair Step",
            "",
            f"- Step: `{report['step']}`",
            f"- Candidate: `{candidate['label']}`",
            f"- Decision: `{candidate['decision']}`",
            f"- Base: `{candidate['cagr']:.4f}` CAGR / `{candidate['max_drawdown']:.4f}` MDD / Sharpe `{candidate['sharpe']:.4f}`",
            f"- Failed gates: `{', '.join(candidate['failed_gates']) if candidate['failed_gates'] else '-'}`",
            f"- Clears overfitting sensitivity: `{gate['clears_overfitting_sensitivity']}`",
            f"- Clears overfitting pass: `{gate['clears_overfitting_pass']}`",
            f"- Clears overfitting flags: `{gate['clears_overfitting_flags']}`",
            f"- Keeps target drawdown: `{gate['keeps_target_drawdown']}`",
            f"- Keeps target CAGR: `{gate['keeps_target_cagr']}`",
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
    elif args.step == "friction_retest":
        report = run_friction_repair_step(args)
    else:
        raise ValueError(f"Unsupported step: {args.step}")
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = args.analysis_dir / f"btc_1d_shallow_liquidity_void_refill_repair_step_{stamp}.json"
    md_path = args.analysis_dir / f"btc_1d_shallow_liquidity_void_refill_repair_step_{stamp}.md"
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
