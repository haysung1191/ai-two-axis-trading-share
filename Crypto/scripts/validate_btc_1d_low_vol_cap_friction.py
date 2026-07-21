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
from scripts.validate_btc_1d_low_vol_cap_candidate import parse_args as parse_validation_args


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run friction sanity check for the BTCUSDT 1d low-volatility cap baseline."
    )
    parser.add_argument("--analysis-dir", type=Path, default=Path("analysis_results"))
    parser.add_argument("--periods", type=int, default=2200)
    parser.add_argument("--cost-levels-bps", nargs="*", type=float, default=[0.0, 8.0, 12.0, 20.0])
    parser.add_argument("--allow-synthetic-ohlcv-fallback", action="store_true")
    return parser


def _run_validation(
    *,
    analysis_dir: Path,
    periods: int,
    cost_bps: float,
    allow_synthetic_ohlcv_fallback: bool,
) -> dict:
    cfg = parse_validation_args(
        [
            "--periods",
            str(periods),
            "--fee-bps",
            str(cost_bps),
            "--slippage-bps",
            str(cost_bps),
            *(["--allow-synthetic-ohlcv-fallback"] if allow_synthetic_ohlcv_fallback else []),
        ]
    )
    return BtcPaperValidationService(analysis_results_dir=analysis_dir).run_validation(cfg)


def _decision(levels: list[dict]) -> tuple[str, str]:
    surviving = [level for level in levels if level["decision"] == "PASS"]
    if not surviving:
        return "pause", "baseline advantage disappears under all tested friction assumptions."
    max_surviving = max(level["cost_bps"] for level in surviving)
    if max_surviving >= 20.0:
        return "continue", "baseline remains paper-valid even under the heaviest tested friction."
    if max_surviving >= 12.0:
        return "continue_with_caution", "baseline survives moderate friction but weakens before the heaviest level."
    return "caution", "baseline survives only under lighter friction assumptions."


def _render_markdown(report: dict) -> str:
    lines = [
        "# BTC 1d Low-Vol Cap Friction Sanity Check",
        "",
        f"- Candidate: `{report['candidate']}`",
        f"- Periods: `{report['periods']}`",
        f"- Final decision: `{report['final_decision']}`",
        f"- Reason: {report['decision_reason']}",
        "",
    ]
    for level in report["levels"]:
        lines.extend(
            [
                f"## {int(level['cost_bps'])} bps fee + {int(level['cost_bps'])} bps slippage",
                f"- decision: `{level['decision']}`",
                f"- sharpe: `{level['sharpe']}`",
                f"- cagr: `{level['cagr']}`",
                f"- max_drawdown: `{level['max_drawdown']}`",
                f"- win_rate: `{level['win_rate']}`",
                f"- trades: `{level['trades']}`",
                f"- failed_gates: `{', '.join(level['failed_gates']) if level['failed_gates'] else '-'}`",
                "",
            ]
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    levels: list[dict] = []
    for cost_bps in args.cost_levels_bps:
        result = _run_validation(
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
                "sharpe": metrics["sharpe"],
                "cagr": metrics["cagr"],
                "max_drawdown": metrics["max_drawdown"],
                "win_rate": metrics["win_rate"],
                "trades": metrics["trades"],
                "failed_gates": decision["failed_gates"],
                "analysis_result_json": result["analysis_result_json"],
            }
        )

    final_decision, reason = _decision(levels)
    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "candidate": "low_vol_cap_050_025_minvol020_p2200",
        "periods": int(args.periods),
        "cost_levels_bps": [float(level) for level in args.cost_levels_bps],
        "levels": levels,
        "final_decision": final_decision,
        "decision_reason": reason,
    }

    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = args.analysis_dir / f"btc_1d_low_vol_cap_friction_{stamp}.json"
    md_path = args.analysis_dir / f"btc_1d_low_vol_cap_friction_{stamp}.md"
    args.analysis_dir.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    print(json.dumps({"report_json_path": str(json_path), "report_md_path": str(md_path), "report": report}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
