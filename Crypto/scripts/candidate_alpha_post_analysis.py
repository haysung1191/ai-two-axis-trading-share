from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.candidate_alpha_overlay_validation import load_candidate_alpha_frame


@dataclass(frozen=True)
class CandidateAlphaPostAnalysisArtifacts:
    report_json_path: Path
    report_md_path: Path
    report: dict[str, Any]


def _latest_analysis_frame(analysis_dir: Path) -> Path:
    candidates = sorted(
        analysis_dir.glob("candidate_alpha_regime_frame_*.csv"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError("No Candidate Alpha frame artifact found")
    return candidates[0]


def load_backtest_artifact(artifact_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    report_path = artifact_dir / "backtest_report.json"
    spec_path = artifact_dir / "spec.json"
    if not report_path.exists():
        raise FileNotFoundError(f"Missing backtest_report.json in {artifact_dir}")
    if not spec_path.exists():
        raise FileNotFoundError(f"Missing spec.json in {artifact_dir}")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    return report, spec


def _interval_to_hours(interval: str) -> int:
    if interval.endswith("h"):
        return int(interval[:-1])
    raise ValueError(f"Unsupported interval for post-analysis join: {interval}")


def build_interval_regime_frame(alpha_frame_1h: pd.DataFrame, interval: str) -> pd.DataFrame:
    hours = _interval_to_hours(interval)
    frame = alpha_frame_1h.copy()
    frame.index = pd.DatetimeIndex(frame.index)
    if hours == 1:
        result = frame[["avoidance_regime", "tradable_regime"]].copy()
        result.index.name = "timestamp"
        return result

    bucket = frame.index.floor(interval)
    grouped = frame.assign(bucket_ts=bucket).groupby("bucket_ts", sort=True)
    result = grouped[["avoidance_regime", "tradable_regime"]].last()
    result.index = pd.DatetimeIndex(result.index)
    result.index.name = "timestamp"
    return result.sort_index(kind="mergesort")


def reconstruct_backtest_timeseries(
    report: dict[str, Any],
    spec: dict[str, Any],
    interval_regime_frame: pd.DataFrame,
) -> pd.DataFrame:
    metadata = spec.get("metadata", {})
    symbols = metadata.get("symbols", report.get("symbols", []))
    if "KRW-BTC" not in symbols:
        raise ValueError("Candidate Alpha descriptive labels currently support only KRW-BTC artifacts")

    equity_curve = report.get("equity_curve", [])
    if not equity_curve:
        raise ValueError("Artifact has no equity_curve to reconstruct")

    interval = metadata.get("ohlcv_interval", "1h")
    length = len(equity_curve)
    if len(interval_regime_frame) < length:
        raise ValueError(
            f"Candidate Alpha regime frame has only {len(interval_regime_frame)} rows for interval {interval}, needs {length}"
        )

    inferred_index = interval_regime_frame.index[-length:]
    reconstructed = pd.DataFrame(index=inferred_index)
    reconstructed.index.name = "timestamp"
    reconstructed["equity_curve"] = pd.Series(equity_curve, index=inferred_index, dtype=float)
    reconstructed["period_return"] = reconstructed["equity_curve"].pct_change()
    cumulative_peaks = reconstructed["equity_curve"].cummax()
    reconstructed["drawdown"] = reconstructed["equity_curve"] / cumulative_peaks - 1.0
    reconstructed["strategy_name"] = report.get("strategy_name")
    reconstructed["artifact_interval"] = interval
    return reconstructed


def load_direct_backtest_timeseries(report: dict[str, Any], spec: dict[str, Any]) -> pd.DataFrame | None:
    metadata = spec.get("metadata", {})
    symbols = metadata.get("symbols", report.get("symbols", []))
    if "KRW-BTC" not in symbols:
        raise ValueError("Candidate Alpha descriptive labels currently support only KRW-BTC artifacts")

    equity_curve = report.get("equity_curve", [])
    equity_timestamps = report.get("equity_timestamps", [])
    if not equity_curve or not equity_timestamps:
        return None
    if len(equity_curve) != len(equity_timestamps):
        raise ValueError("Artifact equity_timestamps length does not match equity_curve length")

    index = pd.to_datetime(equity_timestamps, utc=True)
    direct = pd.DataFrame(index=pd.DatetimeIndex(index))
    direct.index.name = "timestamp"
    direct["equity_curve"] = pd.Series(equity_curve, index=direct.index, dtype=float)
    direct["period_return"] = direct["equity_curve"].pct_change()
    cumulative_peaks = direct["equity_curve"].cummax()
    direct["drawdown"] = direct["equity_curve"] / cumulative_peaks - 1.0
    direct["strategy_name"] = report.get("strategy_name")
    direct["artifact_interval"] = metadata.get("ohlcv_interval", "1h")
    return direct


def join_candidate_alpha_labels(
    reconstructed_backtest: pd.DataFrame,
    interval_regime_frame: pd.DataFrame,
) -> pd.DataFrame:
    labels = interval_regime_frame[["avoidance_regime", "tradable_regime"]].reindex(
        reconstructed_backtest.index,
        method="pad",
    )
    joined = reconstructed_backtest.join(labels, how="left")
    joined["avoidance_regime"] = joined["avoidance_regime"].astype("boolean")
    joined["tradable_regime"] = joined["tradable_regime"].astype("boolean")
    return joined


def summarize_trade_ledger_by_regime(
    trade_ledger: list[dict[str, Any]],
    interval_regime_frame: pd.DataFrame,
) -> dict[str, dict[str, Any]]:
    if not trade_ledger:
        unavailable = {
            "trade_count": None,
            "win_rate": None,
            "mean_trade_pnl": None,
            "median_trade_pnl": None,
            "trade_label_match_ratio": 0.0,
            "trade_level_status": "unavailable: artifact has no timestamped trade ledger",
        }
        return {
            "avoidance_regime": unavailable.copy(),
            "non_avoidance_regime": unavailable.copy(),
        }

    trade_frame = pd.DataFrame(trade_ledger).copy()
    if "entry_timestamp" not in trade_frame.columns:
        unavailable = {
            "trade_count": None,
            "win_rate": None,
            "mean_trade_pnl": None,
            "median_trade_pnl": None,
            "trade_label_match_ratio": 0.0,
            "trade_level_status": "unavailable: trade ledger missing entry_timestamp",
        }
        return {
            "avoidance_regime": unavailable.copy(),
            "non_avoidance_regime": unavailable.copy(),
        }

    trade_frame["entry_timestamp"] = pd.to_datetime(trade_frame["entry_timestamp"], utc=True)
    trade_frame = trade_frame.set_index("entry_timestamp").sort_index(kind="mergesort")
    labels = interval_regime_frame[["avoidance_regime"]].reindex(trade_frame.index, method="pad")
    joined = trade_frame.join(labels, how="left")
    matched = joined["avoidance_regime"].notna().sum()

    def _trade_summary(bucket: pd.DataFrame) -> dict[str, Any]:
        if bucket.empty:
            return {
                "trade_count": 0,
                "win_rate": None,
                "mean_trade_pnl": None,
                "median_trade_pnl": None,
                "trade_label_match_ratio": 0.0,
                "trade_level_status": "available",
            }
        pnl = pd.to_numeric(bucket.get("pnl"), errors="coerce").dropna()
        win_col = bucket.get("win")
        if win_col is not None:
            win_series = win_col.astype(bool)
            win_rate = float(win_series.mean()) if len(win_series) else None
        else:
            win_rate = None
        return {
            "trade_count": int(len(bucket)),
            "win_rate": round(win_rate, 8) if win_rate is not None else None,
            "mean_trade_pnl": round(float(pnl.mean()), 8) if not pnl.empty else None,
            "median_trade_pnl": round(float(pnl.median()), 8) if not pnl.empty else None,
            "trade_label_match_ratio": round(float(bucket["avoidance_regime"].notna().mean()), 8),
            "trade_level_status": "available",
        }

    return {
        "avoidance_regime": _trade_summary(joined[joined["avoidance_regime"] == True]),
        "non_avoidance_regime": _trade_summary(joined[joined["avoidance_regime"] == False]),
        "_coverage": {
            "trade_observation_count": int(len(joined)),
            "matched_trade_label_count": int(matched),
            "matched_trade_label_ratio": round(float(matched / len(joined)), 8) if len(joined) else 0.0,
        },
    }


def _bucket_summary(bucket: pd.DataFrame, trade_summary: dict[str, Any]) -> dict[str, Any]:
    valid_returns = bucket["period_return"].dropna()
    valid_drawdown = bucket["drawdown"].dropna()
    return {
        "observation_count": int(len(bucket)),
        "return_observation_count": int(valid_returns.shape[0]),
        "mean_return": round(float(valid_returns.mean()), 8) if not valid_returns.empty else None,
        "median_return": round(float(valid_returns.median()), 8) if not valid_returns.empty else None,
        "mean_drawdown": round(float(valid_drawdown.mean()), 8) if not valid_drawdown.empty else None,
        "median_drawdown": round(float(valid_drawdown.median()), 8) if not valid_drawdown.empty else None,
        "worst_drawdown": round(float(valid_drawdown.min()), 8) if not valid_drawdown.empty else None,
        "trade_count": trade_summary["trade_count"],
        "win_rate": trade_summary["win_rate"],
        "mean_trade_pnl": trade_summary["mean_trade_pnl"],
        "median_trade_pnl": trade_summary["median_trade_pnl"],
        "trade_label_match_ratio": trade_summary["trade_label_match_ratio"],
        "trade_level_status": trade_summary["trade_level_status"],
    }


def build_post_analysis_report(
    artifact_dir: Path,
    report: dict[str, Any],
    spec: dict[str, Any],
    joined: pd.DataFrame,
    trade_bucket_summary: dict[str, dict[str, Any]],
    *,
    used_direct_timestamps: bool,
) -> dict[str, Any]:
    matched = joined["avoidance_regime"].notna().sum()
    bucket_avoidance = joined[joined["avoidance_regime"] == True]
    bucket_non_avoidance = joined[joined["avoidance_regime"] == False]
    metadata = spec.get("metadata", {})
    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "artifact": {
            "artifact_dir": str(artifact_dir),
            "strategy_name": report.get("strategy_name"),
            "symbols": metadata.get("symbols", report.get("symbols", [])),
            "interval": metadata.get("ohlcv_interval", "1h"),
            "reported_trades": report.get("trades"),
            "reported_win_rate": report.get("win_rate"),
            "reported_max_drawdown": report.get("max_drawdown"),
        },
        "join_coverage": {
            "artifact_observation_count": int(len(joined)),
            "matched_label_count": int(matched),
            "matched_label_ratio": round(float(matched / len(joined)), 8) if len(joined) else 0.0,
            "timestamp_start": joined.index.min().isoformat() if len(joined) else None,
            "timestamp_end": joined.index.max().isoformat() if len(joined) else None,
            "missing_label_count": int(len(joined) - matched),
            "used_direct_timestamps": used_direct_timestamps,
            "trade_observation_count": trade_bucket_summary["_coverage"]["trade_observation_count"],
            "matched_trade_label_count": trade_bucket_summary["_coverage"]["matched_trade_label_count"],
            "matched_trade_label_ratio": trade_bucket_summary["_coverage"]["matched_trade_label_ratio"],
        },
        "bucket_summary": {
            "avoidance_regime": _bucket_summary(bucket_avoidance, trade_bucket_summary["avoidance_regime"]),
            "non_avoidance_regime": _bucket_summary(bucket_non_avoidance, trade_bucket_summary["non_avoidance_regime"]),
        },
        "boundary": {
            "what_it_does": "Attaches Candidate Alpha descriptive labels to an existing backtest result by timestamp join only.",
            "what_it_does_not_do": "Does not alter strategy signals, execution, or runtime behavior.",
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    artifact = report["artifact"]
    coverage = report["join_coverage"]
    avoidance = report["bucket_summary"]["avoidance_regime"]
    non_avoidance = report["bucket_summary"]["non_avoidance_regime"]
    lines = [
        "# Candidate Alpha Post-Analysis Join Report",
        "",
        "## Artifact",
        f"- artifact_dir: {artifact['artifact_dir']}",
        f"- strategy_name: {artifact['strategy_name']}",
        f"- symbols: {artifact['symbols']}",
        f"- interval: {artifact['interval']}",
        f"- reported_trades: {artifact['reported_trades']}",
        f"- reported_win_rate: {artifact['reported_win_rate']}",
        f"- reported_max_drawdown: {artifact['reported_max_drawdown']}",
        "",
        "## Join Coverage",
        f"- artifact_observation_count: {coverage['artifact_observation_count']}",
        f"- matched_label_count: {coverage['matched_label_count']}",
        f"- matched_label_ratio: {coverage['matched_label_ratio']}",
        f"- timestamp_start: {coverage['timestamp_start']}",
        f"- timestamp_end: {coverage['timestamp_end']}",
        f"- missing_label_count: {coverage['missing_label_count']}",
        f"- used_direct_timestamps: {coverage['used_direct_timestamps']}",
        f"- trade_observation_count: {coverage['trade_observation_count']}",
        f"- matched_trade_label_ratio: {coverage['matched_trade_label_ratio']}",
        "",
        "## Avoidance Regime",
        f"- observation_count: {avoidance['observation_count']}",
        f"- mean_return: {avoidance['mean_return']}",
        f"- median_return: {avoidance['median_return']}",
        f"- mean_drawdown: {avoidance['mean_drawdown']}",
        f"- median_drawdown: {avoidance['median_drawdown']}",
        f"- worst_drawdown: {avoidance['worst_drawdown']}",
        f"- trade_count: {avoidance['trade_count']}",
        f"- win_rate: {avoidance['win_rate']}",
        f"- mean_trade_pnl: {avoidance['mean_trade_pnl']}",
        f"- median_trade_pnl: {avoidance['median_trade_pnl']}",
        f"- trade_level_status: {avoidance['trade_level_status']}",
        "",
        "## Non-Avoidance Regime",
        f"- observation_count: {non_avoidance['observation_count']}",
        f"- mean_return: {non_avoidance['mean_return']}",
        f"- median_return: {non_avoidance['median_return']}",
        f"- mean_drawdown: {non_avoidance['mean_drawdown']}",
        f"- median_drawdown: {non_avoidance['median_drawdown']}",
        f"- worst_drawdown: {non_avoidance['worst_drawdown']}",
        f"- trade_count: {non_avoidance['trade_count']}",
        f"- win_rate: {non_avoidance['win_rate']}",
        f"- mean_trade_pnl: {non_avoidance['mean_trade_pnl']}",
        f"- median_trade_pnl: {non_avoidance['median_trade_pnl']}",
        f"- trade_level_status: {non_avoidance['trade_level_status']}",
        "",
        "## Boundary",
        f"- what_it_does: {report['boundary']['what_it_does']}",
        f"- what_it_does_not_do: {report['boundary']['what_it_does_not_do']}",
    ]
    return "\n".join(lines) + "\n"


def run_candidate_alpha_post_analysis(
    artifact_dir: Path,
    analysis_dir: Path,
    *,
    frame_path: Path | None = None,
) -> CandidateAlphaPostAnalysisArtifacts:
    selected_frame_path = frame_path or _latest_analysis_frame(analysis_dir)
    alpha_frame_1h = load_candidate_alpha_frame(selected_frame_path)
    report, spec = load_backtest_artifact(artifact_dir)
    interval = spec.get("metadata", {}).get("ohlcv_interval", "1h")
    interval_regime_frame = build_interval_regime_frame(alpha_frame_1h, interval)
    direct = load_direct_backtest_timeseries(report, spec)
    reconstructed = direct if direct is not None else reconstruct_backtest_timeseries(report, spec, interval_regime_frame)
    joined = join_candidate_alpha_labels(reconstructed, interval_regime_frame)
    trade_bucket_summary = summarize_trade_ledger_by_regime(report.get("trade_ledger", []), interval_regime_frame)
    final_report = build_post_analysis_report(
        artifact_dir,
        report,
        spec,
        joined,
        trade_bucket_summary,
        used_direct_timestamps=direct is not None,
    )

    analysis_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    report_json_path = analysis_dir / f"candidate_alpha_post_analysis_{artifact_dir.name}_{stamp}.json"
    report_md_path = analysis_dir / f"candidate_alpha_post_analysis_{artifact_dir.name}_{stamp}.md"
    report_json_path.write_text(json.dumps(final_report, indent=2), encoding="utf-8")
    report_md_path.write_text(render_markdown(final_report), encoding="utf-8")

    return CandidateAlphaPostAnalysisArtifacts(
        report_json_path=report_json_path,
        report_md_path=report_md_path,
        report=final_report,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Attach Candidate Alpha descriptive regime labels to an existing backtest artifact by timestamp join.")
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument("--analysis-dir", default="analysis_results")
    parser.add_argument("--frame-path", default=None)
    args = parser.parse_args()

    artifacts = run_candidate_alpha_post_analysis(
        artifact_dir=Path(args.artifact_dir),
        analysis_dir=Path(args.analysis_dir),
        frame_path=Path(args.frame_path) if args.frame_path else None,
    )
    print(json.dumps({
        "report_json_path": str(artifacts.report_json_path),
        "report_md_path": str(artifacts.report_md_path),
        "join_coverage": artifacts.report["join_coverage"],
        "bucket_summary": artifacts.report["bucket_summary"],
        "boundary": artifacts.report["boundary"],
    }, indent=2))


if __name__ == "__main__":
    main()
