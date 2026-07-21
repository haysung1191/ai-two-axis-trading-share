from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _unwrap(payload: dict[str, Any]) -> dict[str, Any]:
    if "report" in payload and isinstance(payload["report"], dict):
        return payload["report"]
    return payload


def _latest_json(analysis_dir: Path, pattern: str) -> Path:
    matches = sorted(analysis_dir.glob(pattern), key=lambda path: path.stat().st_mtime, reverse=True)
    if not matches:
        raise FileNotFoundError(f"No files matched {pattern} in {analysis_dir}")
    return matches[0]


def _latest_matching_json(analysis_dir: Path, pattern: str, predicate) -> Path:
    matches = sorted(analysis_dir.glob(pattern), key=lambda path: path.stat().st_mtime, reverse=True)
    for path in matches:
        payload = _unwrap(_load_json(path))
        if predicate(payload):
            return path
    raise FileNotFoundError(f"No files matched {pattern} with predicate in {analysis_dir}")


def _select_practical_paper_validation(analysis_dir: Path) -> Path:
    explicit_patterns = [
        "btc_1d_volatility_expansion_reclaim_stab_atrs_btcusdt_1d_2200_paper_validation_*.json",
        "btc_1d_volatility_expansion_reclaim_stab_atrs_btcusdt_1d_2200_0bps_paper_validation_*.json",
    ]
    for pattern in explicit_patterns:
        matches = sorted(analysis_dir.glob(pattern), key=lambda path: path.stat().st_mtime, reverse=True)
        if matches:
            return matches[0]

    generic_pattern = "btc_1d_volatility_expansion_reclaim_stab_atrs_paper_validation_*.json"
    try:
        return _latest_matching_json(
            analysis_dir,
            generic_pattern,
            lambda payload: str(payload.get("config", {}).get("symbol", "")).upper() == "BTCUSDT",
        )
    except FileNotFoundError:
        return _latest_json(analysis_dir, generic_pattern)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Publish the BTC 1d practical scorecard.")
    parser.add_argument("--analysis-dir", type=Path, default=Path("analysis_results"))
    return parser


def _scorecard_payload(analysis_dir: Path) -> tuple[dict[str, Any], dict[str, str]]:
    paper_path = _select_practical_paper_validation(analysis_dir)
    friction_path = _latest_json(analysis_dir, "btc_1d_volatility_expansion_reclaim_stab_atrs_friction_*.json")
    benchmark_path = _latest_json(analysis_dir, "btc_1d_volatility_expansion_reclaim_stab_atrs_benchmark_stats_*.json")
    stats_path = _latest_json(analysis_dir, "btc_1d_volatility_expansion_reclaim_stab_atrs_stats_*.json")
    regime_path = _latest_json(analysis_dir, "btc_1d_volatility_expansion_reclaim_stab_atrs_regime_stability_*.json")
    concentration_path = _latest_json(analysis_dir, "btc_1d_volatility_expansion_reclaim_stab_atrs_concentration_*.json")

    paper = _unwrap(_load_json(paper_path))
    friction = _unwrap(_load_json(friction_path))
    benchmark = _unwrap(_load_json(benchmark_path))
    stats = _unwrap(_load_json(stats_path))
    regime = _unwrap(_load_json(regime_path))
    concentration = _unwrap(_load_json(concentration_path))

    btc_symbol = next(item for item in benchmark["symbols"] if item["symbol"] == "BTCUSDT")
    eth_symbol = next(item for item in benchmark["symbols"] if item["symbol"] == "ETHUSDT")
    heavy_friction = friction["levels"][-1]

    payload = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "candidate": "volatility_expansion_reclaim_lower_atr_window_tighter_stop",
        "decision": "paper_ready_btc_only_with_caveats",
        "status_label": "btc_only_practical_with_caveats",
        "summary": {
            "scope": "BTC-only",
            "paper_decision": paper["decision_record"]["decision"],
            "carry_metrics": paper["decision_record"]["key_metrics"],
            "friction_20bps_decision": heavy_friction["decision"],
            "friction_20bps_metrics": {
                "sharpe": heavy_friction["sharpe"],
                "cagr": heavy_friction["cagr"],
                "max_drawdown": heavy_friction["max_drawdown"],
            },
        },
        "benchmark": {
            "btc": btc_symbol,
            "eth": eth_symbol,
        },
        "statistical_defense": stats["statistics"],
        "bootstrap": stats["bootstrap"],
        "regime": regime["regime_metrics"],
        "leave_one_year_out": regime["leave_one_year_out"],
        "concentration": concentration,
        "risks": [
            "BTC-only practical model; ETH generalization is weak.",
            "DSR remains weak under selection-trials adjustment.",
            "Range and low-volatility regime behavior is weak.",
            "Top 5 trades contribute a large share of positive trade PnL.",
        ],
        "source_artifacts": {
            "paper_validation": str(paper_path),
            "friction": str(friction_path),
            "benchmark_stats": str(benchmark_path),
            "stats": str(stats_path),
            "regime_stability": str(regime_path),
            "concentration": str(concentration_path),
        },
    }
    return payload, {
        "paper_validation": str(paper_path),
        "friction": str(friction_path),
        "benchmark_stats": str(benchmark_path),
        "stats": str(stats_path),
        "regime_stability": str(regime_path),
        "concentration": str(concentration_path),
    }


def _render_markdown(payload: dict[str, Any]) -> str:
    carry = payload["summary"]["carry_metrics"]
    friction = payload["summary"]["friction_20bps_metrics"]
    btc = payload["benchmark"]["btc"]
    eth = payload["benchmark"]["eth"]
    stats = payload["statistical_defense"]
    bootstrap = payload["bootstrap"]
    regime = payload["regime"]["regimes"]
    leave = payload["leave_one_year_out"]
    trade_conc = payload["concentration"]["trade_concentration"]
    month_conc = payload["concentration"]["monthly_concentration"]
    eth_buyhold_paired_p = eth["benchmarks"][0]["paired_bootstrap"]["p_diff_mean_gt_0"]
    return "\n".join(
        [
            "# BTC 1d Practical Scorecard",
            "",
            f"- Candidate: `{payload['candidate']}`",
            f"- Decision: `{payload['decision']}`",
            f"- Status label: `{payload['status_label']}`",
            f"- Scope: `{payload['summary']['scope']}`",
            f"- Quick read: `BTC-only practical` | ETH buy&hold paired `P(diff>0)={eth_buyhold_paired_p:.4f}` | ETH generalization weak",
            "",
            "## Core",
            f"- paper: `{payload['summary']['paper_decision']}` | Sharpe `{carry['sharpe']:.4f}` | CAGR `{carry['cagr'] * 100:.2f}%` | MDD `{carry['max_drawdown'] * 100:.2f}%` | trades `{int(carry['trades'])}`",
            f"- 20bps friction: `{payload['summary']['friction_20bps_decision']}` | Sharpe `{friction['sharpe']:.4f}` | CAGR `{friction['cagr'] * 100:.2f}%` | MDD `{friction['max_drawdown'] * 100:.2f}%`",
            "",
            "## Benchmarks",
            f"- BTC leader vs buy&hold: leader Sharpe `{btc['leader']['sharpe']:.4f}` vs benchmark `{btc['benchmarks'][0]['metrics']['sharpe']:.4f}` | leader MDD `{btc['leader']['max_drawdown'] * 100:.2f}%` vs benchmark `{btc['benchmarks'][0]['metrics']['max_drawdown'] * 100:.2f}%`",
            f"- ETH generalization: leader Sharpe `{eth['leader']['sharpe']:.4f}` | buy&hold paired P(diff>0) `{eth['benchmarks'][0]['paired_bootstrap']['p_diff_mean_gt_0']:.4f}`",
            "",
            "## Statistical Defense",
            f"- PSR `{stats['psr']:.4f}` | DSR `{stats['dsr']:.4f}` | DSR hurdle Sharpe `{stats['dsr_hurdle_sharpe']:.4f}`",
            f"- bootstrap Sharpe 95% CI `[{bootstrap['sharpe_ci_95'][0]:.4f}, {bootstrap['sharpe_ci_95'][1]:.4f}]`",
            f"- bootstrap CAGR 95% CI `[{bootstrap['cagr_ci_95'][0] * 100:.2f}%, {bootstrap['cagr_ci_95'][1] * 100:.2f}%]`",
            "",
            "## Regime",
            f"- high_volatility Sharpe `{regime['high_volatility']['sharpe']:.4f}`",
            f"- low_volatility Sharpe `{regime['low_volatility']['sharpe']:.4f}`",
            f"- range Sharpe `{regime['range']['sharpe']:.4f}`",
            f"- worst leave-one-year-out CAGR year `{leave['worst_cagr_year']}`",
            f"- worst leave-one-year-out MDD year `{leave['worst_mdd_year']}`",
            "",
            "## Concentration",
            f"- top 1 trade share `{trade_conc['top_1_trade_share']:.4f}`",
            f"- top 3 trade share `{trade_conc['top_3_trade_share']:.4f}`",
            f"- top 5 trade share `{trade_conc['top_5_trade_share']:.4f}`",
            f"- top 5 month share `{month_conc['top_5_month_share']:.4f}`",
            "",
            "## Risks",
            *[f"- {risk}" for risk in payload["risks"]],
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload, _ = _scorecard_payload(args.analysis_dir)

    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = args.analysis_dir / f"btc_1d_practical_scorecard_{stamp}.json"
    md_path = args.analysis_dir / f"btc_1d_practical_scorecard_{stamp}.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(payload), encoding="utf-8")

    latest_json = args.analysis_dir / "btc_1d_practical_scorecard_latest.json"
    latest_md = args.analysis_dir / "btc_1d_practical_scorecard_md_latest.md"
    shutil.copyfile(json_path, latest_json)
    shutil.copyfile(md_path, latest_md)

    print(
        json.dumps(
            {
                "scorecard_json_path": str(json_path),
                "scorecard_md_path": str(md_path),
                "scorecard_json_latest": str(latest_json),
                "scorecard_md_latest": str(latest_md),
                "scorecard": payload,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
