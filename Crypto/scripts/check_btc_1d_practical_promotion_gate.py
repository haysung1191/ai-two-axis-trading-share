from __future__ import annotations

import argparse
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check the latest BTC 1d practical scorecard against promotion gates.")
    parser.add_argument("--analysis-dir", type=Path, default=Path("analysis_results"))
    parser.add_argument("--expected-scope", default="BTC-only")
    parser.add_argument("--required-paper-decision", default="PASS")
    parser.add_argument("--required-friction-decision", default="PASS")
    parser.add_argument("--min-btc-sharpe", type=float, default=1.0)
    parser.add_argument("--max-btc-mdd", type=float, default=0.20)
    parser.add_argument("--min-psr", type=float, default=0.95)
    parser.add_argument("--min-bootstrap-p-sharpe", type=float, default=0.95)
    parser.add_argument("--min-dsr", type=float, default=0.05)
    parser.add_argument("--min-range-sharpe", type=float, default=0.0)
    parser.add_argument("--max-top-5-trade-share", type=float, default=0.60)
    parser.add_argument("--min-eth-buyhold-paired-p", type=float, default=0.50)
    return parser


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _latest_json(analysis_dir: Path, pattern: str) -> Path:
    matches = sorted(analysis_dir.glob(pattern), key=lambda path: path.stat().st_mtime, reverse=True)
    if not matches:
        raise FileNotFoundError(f"No files matched {pattern} in {analysis_dir}")
    return matches[0]


def _evaluate_post_spike_fallback(*, analysis_dir: Path, args: argparse.Namespace, reason: str) -> dict[str, Any]:
    paper_path = _latest_json(
        analysis_dir,
        "btc_1d_post_spike_consolidation_breakout_v4_*paper_validation_*.json",
    )
    friction_path = analysis_dir / "btc_1d_post_spike_consolidation_breakout_friction_latest.json"
    paper = _load_json(paper_path)
    friction = _load_json(friction_path)

    decision_record = paper["decision_record"]
    carry_metrics = decision_record["key_metrics"]
    levels = friction.get("levels") or []
    heaviest = max(levels, key=lambda row: float(row["cost_bps"])) if levels else {}

    failures: list[str] = []
    caveats = [f"fallback_without_legacy_scorecard: {reason}", "statistical_defense_not_available_in_fallback"]

    if decision_record.get("decision") != args.required_paper_decision:
        failures.append(
            f"paper decision mismatch: expected {args.required_paper_decision}, got {decision_record.get('decision')}"
        )
    if heaviest.get("decision") != args.required_friction_decision:
        failures.append(
            "heaviest friction mismatch: "
            f"expected {args.required_friction_decision}, got {heaviest.get('decision')}"
        )
    if float(carry_metrics["sharpe"]) < args.min_btc_sharpe:
        failures.append(f"btc sharpe below floor: {carry_metrics['sharpe']:.4f} < {args.min_btc_sharpe:.4f}")
    if float(carry_metrics["max_drawdown"]) > args.max_btc_mdd:
        failures.append(
            "btc max drawdown above ceiling: "
            f"{carry_metrics['max_drawdown']:.4f} > {args.max_btc_mdd:.4f}"
        )
    if float(heaviest.get("cost_bps", 0.0)) < 20.0:
        failures.append(f"heaviest friction below 20bps: {float(heaviest.get('cost_bps', 0.0)):.1f}")

    decision = "hold_not_promotable" if failures else "btc_only_practical_with_caveats"
    return {
        "ok": not failures,
        "decision": decision,
        "status_label": decision,
        "candidate": friction.get("candidate", paper.get("config", {}).get("strategy_name")),
        "scope": args.expected_scope,
        "paper_decision": decision_record.get("decision"),
        "friction_20bps_decision": heaviest.get("decision"),
        "carry_metrics": carry_metrics,
        "btc_benchmark_leader_sharpe": None,
        "psr": None,
        "dsr": None,
        "bootstrap_p_sharpe_gt_0": None,
        "range_regime_sharpe": None,
        "top_5_trade_share": None,
        "eth_leader_sharpe": None,
        "eth_buyhold_paired_p_diff_gt_0": None,
        "failures": failures,
        "caveats": caveats,
        "source_scorecard": None,
        "source_artifacts": {
            "paper_validation": str(paper_path),
            "friction": str(friction_path),
        },
    }


def evaluate_practical_promotion_gate(*, analysis_dir: Path, args: argparse.Namespace) -> dict[str, Any]:
    scorecard_path = analysis_dir / "btc_1d_practical_scorecard_latest.json"
    scorecard = _load_json(scorecard_path)

    if scorecard.get("status") == "unavailable":
        return _evaluate_post_spike_fallback(
            analysis_dir=analysis_dir,
            args=args,
            reason=str(scorecard.get("reason", "scorecard_unavailable")),
        )

    failures: list[str] = []
    caveats: list[str] = []

    summary = scorecard["summary"]
    btc = scorecard["benchmark"]["btc"]
    eth = scorecard["benchmark"].get("eth")
    stats = scorecard["statistical_defense"]
    bootstrap = scorecard["bootstrap"]
    regime = scorecard["regime"]["regimes"]
    concentration = scorecard["concentration"]["trade_concentration"]

    if summary["scope"] != args.expected_scope:
        failures.append(f"scope mismatch: expected {args.expected_scope}, got {summary['scope']}")
    if summary["paper_decision"] != args.required_paper_decision:
        failures.append(
            f"paper decision mismatch: expected {args.required_paper_decision}, got {summary['paper_decision']}"
        )
    if summary["friction_20bps_decision"] != args.required_friction_decision:
        failures.append(
            "20bps friction mismatch: "
            f"expected {args.required_friction_decision}, got {summary['friction_20bps_decision']}"
        )
    if float(summary["carry_metrics"]["sharpe"]) < args.min_btc_sharpe:
        failures.append(
            f"btc sharpe below floor: {summary['carry_metrics']['sharpe']:.4f} < {args.min_btc_sharpe:.4f}"
        )
    if float(summary["carry_metrics"]["max_drawdown"]) > args.max_btc_mdd:
        failures.append(
            "btc max drawdown above ceiling: "
            f"{summary['carry_metrics']['max_drawdown']:.4f} > {args.max_btc_mdd:.4f}"
        )

    leader_sharpe = float(btc["leader"]["sharpe"])
    for benchmark in btc["benchmarks"]:
        benchmark_sharpe = float(benchmark["metrics"]["sharpe"])
        if leader_sharpe <= benchmark_sharpe:
            failures.append(
                f"btc leader sharpe not above {benchmark['label']}: {leader_sharpe:.4f} <= {benchmark_sharpe:.4f}"
            )

    if float(stats["psr"]) < args.min_psr:
        failures.append(f"psr below floor: {stats['psr']:.4f} < {args.min_psr:.4f}")
    if float(bootstrap["p_sharpe_gt_0"]) < args.min_bootstrap_p_sharpe:
        failures.append(
            "bootstrap p(sharpe>0) below floor: "
            f"{bootstrap['p_sharpe_gt_0']:.4f} < {args.min_bootstrap_p_sharpe:.4f}"
        )

    if float(stats["dsr"]) < args.min_dsr:
        caveats.append(f"dsr below floor: {stats['dsr']:.4f} < {args.min_dsr:.4f}")
    if float(regime["range"]["sharpe"]) < args.min_range_sharpe:
        caveats.append(
            f"range regime sharpe below floor: {regime['range']['sharpe']:.4f} < {args.min_range_sharpe:.4f}"
        )
    if float(concentration["top_5_trade_share"]) > args.max_top_5_trade_share:
        caveats.append(
            "top 5 trade share above ceiling: "
            f"{concentration['top_5_trade_share']:.4f} > {args.max_top_5_trade_share:.4f}"
        )
    eth_buyhold_paired_p = None
    eth_leader_sharpe = None
    if eth:
        eth_leader_sharpe = float(eth["leader"]["sharpe"])
        buyhold_benchmark = next((item for item in eth["benchmarks"] if item["label"] == "buy_and_hold"), None)
        if buyhold_benchmark is not None:
            eth_buyhold_paired_p = float(buyhold_benchmark["paired_bootstrap"]["p_diff_mean_gt_0"])
            if eth_buyhold_paired_p < args.min_eth_buyhold_paired_p:
                caveats.append(
                    "eth buy&hold paired p(diff>0) below floor: "
                    f"{eth_buyhold_paired_p:.4f} < {args.min_eth_buyhold_paired_p:.4f}"
                )

    if failures:
        decision = "hold_not_promotable"
    elif caveats:
        decision = "btc_only_practical_with_caveats"
    else:
        decision = "promotable_btc_only_practical"

    return {
        "ok": not failures,
        "decision": decision,
        "status_label": decision,
        "candidate": scorecard["candidate"],
        "scope": summary["scope"],
        "paper_decision": summary["paper_decision"],
        "friction_20bps_decision": summary["friction_20bps_decision"],
        "carry_metrics": summary["carry_metrics"],
        "btc_benchmark_leader_sharpe": leader_sharpe,
        "psr": stats["psr"],
        "dsr": stats["dsr"],
        "bootstrap_p_sharpe_gt_0": bootstrap["p_sharpe_gt_0"],
        "range_regime_sharpe": regime["range"]["sharpe"],
        "top_5_trade_share": concentration["top_5_trade_share"],
        "eth_leader_sharpe": eth_leader_sharpe,
        "eth_buyhold_paired_p_diff_gt_0": eth_buyhold_paired_p,
        "failures": failures,
        "caveats": caveats,
        "source_scorecard": str(scorecard_path),
    }


def render_practical_promotion_gate(result: dict[str, Any]) -> str:
    status = "PASS" if result["ok"] else "FAIL"
    lines = [
        "# BTC 1d Practical Promotion Gate",
        "",
        f"- status: `{status}`",
        f"- decision: `{result['decision']}`",
        f"- status_label: `{result['status_label']}`",
        f"- candidate: `{result['candidate']}`",
        f"- scope: `{result['scope']}`",
        f"- paper: `{result['paper_decision']}`",
        f"- friction_20bps: `{result['friction_20bps_decision']}`",
        f"- sharpe: `{result['carry_metrics']['sharpe']:.4f}`",
        f"- cagr: `{result['carry_metrics']['cagr'] * 100:.2f}%`",
        f"- mdd: `{result['carry_metrics']['max_drawdown'] * 100:.2f}%`",
    ]
    if result["psr"] is not None:
        lines.append(f"- psr: `{result['psr']:.4f}`")
    if result["dsr"] is not None:
        lines.append(f"- dsr: `{result['dsr']:.4f}`")
    if result["bootstrap_p_sharpe_gt_0"] is not None:
        lines.append(f"- bootstrap_p_sharpe_gt_0: `{result['bootstrap_p_sharpe_gt_0']:.4f}`")
    if result["range_regime_sharpe"] is not None:
        lines.append(f"- range_regime_sharpe: `{result['range_regime_sharpe']:.4f}`")
    if result["top_5_trade_share"] is not None:
        lines.append(f"- top_5_trade_share: `{result['top_5_trade_share']:.4f}`")
    if result["eth_buyhold_paired_p_diff_gt_0"] is not None:
        lines.append(f"- eth_buyhold_paired_p_diff_gt_0: `{result['eth_buyhold_paired_p_diff_gt_0']:.4f}`")
    if result["eth_leader_sharpe"] is not None:
        lines.append(f"- eth_leader_sharpe: `{result['eth_leader_sharpe']:.4f}`")
    if result["failures"]:
        lines.append("")
        lines.append("## Failures")
        lines.extend(f"- {failure}" for failure in result["failures"])
    if result["caveats"]:
        lines.append("")
        lines.append("## Caveats")
        lines.extend(f"- {caveat}" for caveat in result["caveats"])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = evaluate_practical_promotion_gate(analysis_dir=args.analysis_dir, args=args)

    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = args.analysis_dir / f"btc_1d_practical_promotion_gate_{stamp}.json"
    md_path = args.analysis_dir / f"btc_1d_practical_promotion_gate_{stamp}.md"
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    md_path.write_text(render_practical_promotion_gate(result), encoding="utf-8")

    latest_json = args.analysis_dir / "btc_1d_practical_promotion_gate_latest.json"
    latest_md = args.analysis_dir / "btc_1d_practical_promotion_gate_md_latest.md"
    shutil.copyfile(json_path, latest_json)
    shutil.copyfile(md_path, latest_md)

    print(
        json.dumps(
            {
                "promotion_gate_json_path": str(json_path),
                "promotion_gate_md_path": str(md_path),
                "promotion_gate_json_latest": str(latest_json),
                "promotion_gate_md_latest": str(latest_md),
                "promotion_gate": result,
            },
            indent=2,
        )
    )
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
