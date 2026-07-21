from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.candidate_alpha_overlay_robustness import run_candidate_alpha_overlay_robustness
from scripts.candidate_alpha_overlay_validation import run_candidate_alpha_overlay_validation
from scripts.candidate_alpha_regime_report import fetch_binance_1h, fetch_bithumb_1h, run_candidate_alpha_regime_report


@dataclass(frozen=True)
class CandidateAlphaExtendedWindowArtifacts:
    report_json_path: Path
    report_md_path: Path
    report: dict[str, Any]


def _history_window() -> dict[str, Any]:
    krw_btc = fetch_bithumb_1h("BTC")
    krw_usdt = fetch_bithumb_1h("USDT")
    binance_btc = fetch_binance_1h("BTCUSDT", limit=5000)

    common_start = max(krw_btc.index.min(), krw_usdt.index.min(), binance_btc.index.min())
    common_end = min(krw_btc.index.max(), krw_usdt.index.max(), binance_btc.index.max())

    krw_btc_common = krw_btc.loc[(krw_btc.index >= common_start) & (krw_btc.index <= common_end)]
    krw_usdt_common = krw_usdt.loc[(krw_usdt.index >= common_start) & (krw_usdt.index <= common_end)]
    binance_common = binance_btc.loc[(binance_btc.index >= common_start) & (binance_btc.index <= common_end)]
    common_index = krw_btc_common.index.intersection(krw_usdt_common.index).intersection(binance_common.index)

    return {
        "bithumb_krw_btc_rows": int(len(krw_btc)),
        "bithumb_krw_btc_start": krw_btc.index.min().isoformat(),
        "bithumb_krw_btc_end": krw_btc.index.max().isoformat(),
        "bithumb_krw_usdt_rows": int(len(krw_usdt)),
        "bithumb_krw_usdt_start": krw_usdt.index.min().isoformat(),
        "bithumb_krw_usdt_end": krw_usdt.index.max().isoformat(),
        "binance_btcusdt_rows": int(len(binance_btc)),
        "binance_btcusdt_start": binance_btc.index.min().isoformat(),
        "binance_btcusdt_end": binance_btc.index.max().isoformat(),
        "common_start": common_start.isoformat(),
        "common_end": common_end.isoformat(),
        "common_rows": int(len(common_index)),
    }


def render_extended_window_markdown(report: dict[str, Any]) -> str:
    history = report["history_window"]
    overlay = report.get("overlay_validation")
    robustness = report.get("overlay_robustness")
    lines = [
        "# Candidate Alpha Extended Window Robustness Report",
        "",
        "## Available Common History Window",
        f"- bithumb_krw_btc_rows: {history['bithumb_krw_btc_rows']}",
        f"- bithumb_krw_usdt_rows: {history['bithumb_krw_usdt_rows']}",
        f"- binance_btcusdt_rows: {history['binance_btcusdt_rows']}",
        f"- common_start: {history['common_start']}",
        f"- common_end: {history['common_end']}",
        f"- common_rows: {history['common_rows']}",
        "",
    ]
    if overlay is None or robustness is None:
        lines.extend(
            [
                "## Limitation",
                "- Longer common window could not be built, so overlay robustness could not be extended.",
                "",
                "## Final Decision",
                f"- decision: {report['final_decision']}",
                f"- reason: {report['decision_reason']}",
            ]
        )
        return "\n".join(lines) + "\n"

    baseline = overlay["comparison"]["baseline"]
    filtered = overlay["comparison"]["baseline_plus_candidate_alpha_avoidance_filter"]
    lines.extend(
        [
            "## Full Sample Comparison",
            f"- baseline sharpe: {baseline['sharpe']}",
            f"- overlay sharpe: {filtered['sharpe']}",
            f"- baseline cagr: {baseline['cagr']}",
            f"- overlay cagr: {filtered['cagr']}",
            f"- baseline trades: {baseline['trades']}",
            f"- overlay trades: {filtered['trades']}",
            f"- baseline win_rate: {baseline['win_rate']}",
            f"- overlay win_rate: {filtered['win_rate']}",
            f"- baseline max_drawdown: {baseline['max_drawdown']}",
            f"- overlay max_drawdown: {filtered['max_drawdown']}",
            "",
            "## Chunked Robustness",
            f"- sharpe improved chunks: {robustness['consistency']['sharpe_improved_chunks']}",
            f"- cagr improved chunks: {robustness['consistency']['cagr_improved_chunks']}",
            f"- win_rate improved chunks: {robustness['consistency']['win_rate_improved_chunks']}",
            f"- drawdown improved chunks: {robustness['consistency']['drawdown_improved_chunks']}",
            "",
            "## Final Decision",
            f"- decision: {report['final_decision']}",
            f"- reason: {report['decision_reason']}",
        ]
    )
    return "\n".join(lines) + "\n"


def run_candidate_alpha_extended_window_report(analysis_dir: Path) -> CandidateAlphaExtendedWindowArtifacts:
    history = _history_window()
    analysis_dir.mkdir(parents=True, exist_ok=True)

    if history["common_rows"] <= 1000:
        report = {
            "generated_at": datetime.now(tz=UTC).isoformat(),
            "history_window": history,
            "overlay_validation": None,
            "overlay_robustness": None,
            "final_decision": "pause",
            "decision_reason": "No meaningfully longer common 1h window was available beyond the current sample.",
        }
    else:
        regime_artifacts = run_candidate_alpha_regime_report(analysis_dir, max_rows=history["common_rows"])
        overlay_artifacts = run_candidate_alpha_overlay_validation(
            analysis_dir,
            frame_path=regime_artifacts.aligned_frame_csv_path,
        )
        robustness_artifacts = run_candidate_alpha_overlay_robustness(
            analysis_dir,
            frame_path=regime_artifacts.aligned_frame_csv_path,
            chunks=3,
        )
        report = {
            "generated_at": datetime.now(tz=UTC).isoformat(),
            "history_window": history,
            "regime_frame_path": str(regime_artifacts.aligned_frame_csv_path),
            "overlay_validation": overlay_artifacts.report,
            "overlay_robustness": robustness_artifacts.memo,
            "final_decision": robustness_artifacts.memo["final_decision"],
            "decision_reason": robustness_artifacts.memo["decision_reason"],
        }

    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    report_json_path = analysis_dir / f"candidate_alpha_extended_window_{stamp}.json"
    report_md_path = analysis_dir / f"candidate_alpha_extended_window_{stamp}.md"
    report_json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    report_md_path.write_text(render_extended_window_markdown(report), encoding="utf-8")
    return CandidateAlphaExtendedWindowArtifacts(report_json_path=report_json_path, report_md_path=report_md_path, report=report)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extend Candidate Alpha overlay validation to the longest common history window.")
    parser.add_argument("--analysis-dir", default="analysis_results")
    args = parser.parse_args()

    artifacts = run_candidate_alpha_extended_window_report(Path(args.analysis_dir))
    print(
        json.dumps(
            {
                "report_json_path": str(artifacts.report_json_path),
                "report_md_path": str(artifacts.report_md_path),
                "history_window": artifacts.report["history_window"],
                "final_decision": artifacts.report["final_decision"],
                "decision_reason": artifacts.report["decision_reason"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
