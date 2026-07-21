from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.manual_trade_brief import load_manual_brief
from src.manual.materiality import build_policy_materiality_summary


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid JSON object: {path}")
    return payload


def _find_latest(root: Path, relative_parts: list[str]) -> Path:
    matches = sorted(
        root.rglob(relative_parts[-1]),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for path in matches:
        if list(path.parts[-len(relative_parts):]) == relative_parts:
            return path
    raise FileNotFoundError(f"Could not find {'/'.join(relative_parts)} under {root}")


def _resolve_snapshot_artifact_path(value: Any) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    path = Path(value)
    return path if path.exists() else None


def _iso_to_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def build_manual_daily_summary(
    *,
    artifacts_dir: Path,
    reexport_dir: Path,
    logs_dir: Path,
    run_id: str | None = None,
) -> dict[str, Any]:
    manual_brief_payload = load_manual_brief(logs_dir, run_id=run_id)
    snapshot_metadata = manual_brief_payload.get("metadata", {})

    approved_path = _resolve_snapshot_artifact_path(snapshot_metadata.get("approved_strategy_path")) or _find_latest(
        artifacts_dir,
        ["approved_strategy.json"],
    )
    bundle_path = _resolve_snapshot_artifact_path(snapshot_metadata.get("policy_bundle_path")) or _find_latest(
        reexport_dir,
        ["publish", "policy_bundle.json"],
    )
    approved = _load_json(approved_path)
    bundle = _load_json(bundle_path)

    winner = (approved.get("winners") or [{}])[0]
    strategy = (bundle.get("strategies") or [{}])[0]
    now = datetime.now(tz=UTC)
    valid_until = _iso_to_dt(strategy.get("valid_until"))
    brief_run_at = _iso_to_dt(manual_brief_payload.get("candle_close_utc"))
    bundle_source_run_id = bundle.get("source_run_id")

    warnings: list[str] = []
    if not winner.get("parameters"):
        warnings.append("Approved strategy parameters are empty; inspect research payload fidelity.")
    if valid_until is not None and valid_until < now:
        warnings.append("Policy bundle valid_until is in the past.")
    if not bundle.get("bundle_id"):
        warnings.append("Policy bundle_id is missing.")
    if not strategy.get("strategy_id"):
        warnings.append("Policy strategy_id is missing from the latest bundle.")
    if not strategy.get("symbol_scope"):
        warnings.append("Policy bundle symbol_scope is empty.")
    if winner.get("source_run_id") and bundle_source_run_id and winner.get("source_run_id") != bundle_source_run_id:
        warnings.append("Approved strategy source_run_id does not match the latest policy bundle source_run_id.")
    if winner.get("strategy_id") and strategy.get("strategy_id") and winner.get("strategy_id") != strategy.get("strategy_id"):
        warnings.append("Approved strategy_id does not match the latest policy bundle strategy_id.")
    if brief_run_at is not None and (now - brief_run_at).total_seconds() > 48 * 3600:
        warnings.append("Latest manual brief is older than 48 hours; treat watchlist output as stale.")
    if str(manual_brief_payload.get("source_metadata", {}).get("source_kind")) == "legacy_signals":
        warnings.append("Latest manual brief was reconstructed from legacy signals; some price/stop/target fields may be missing.")
    brief_summary = manual_brief_payload["manual_brief"].get("summary", {})
    market_filter = snapshot_metadata.get("market_filter", {}) if isinstance(snapshot_metadata, dict) else {}
    counterfactual_buys = snapshot_metadata.get("counterfactual_buys_without_market_filter", []) if isinstance(snapshot_metadata, dict) else []
    policy_materiality = build_policy_materiality_summary(
        recommendations=manual_brief_payload.get("manual_recommendations", []),
        snapshot_metadata=snapshot_metadata if isinstance(snapshot_metadata, dict) else {},
    )
    if int(brief_summary.get("scheduled_due_to_policy_count", 0)) == 0:
        warnings.append("Latest manual brief shows no direct policy-driven scheduling reversal.")
    if market_filter.get("below_ema"):
        warnings.append(
            f"Market filter is active: {market_filter.get('symbol', 'BTC')} close {market_filter.get('close')} is below EMA{market_filter.get('ema_period')} {market_filter.get('ema')}."
        )
        if counterfactual_buys:
            warnings.append(
                f"Without the market filter, {len(counterfactual_buys)} candidate(s) would sit inside the active top-{len(counterfactual_buys)} cutoff."
            )

    return {
        "generated_at": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "sources": {
            "approved_strategy_path": str(approved_path),
            "policy_bundle_path": str(bundle_path),
            "manual_brief_source": str(manual_brief_payload["summary_path"]),
            "manual_brief_source_kind": str(manual_brief_payload.get("source_metadata", {}).get("source_kind", "unknown")),
            "manual_brief_mtime_utc": manual_brief_payload.get("source_metadata", {}).get("summary_mtime_utc"),
        },
        "strategy_snapshot": {
            "strategy_id": winner.get("strategy_id"),
            "source_run_id": winner.get("source_run_id"),
            "symbol": winner.get("symbol"),
            "timeframe": winner.get("timeframe"),
            "parameters": winner.get("parameters", {}),
            "metrics": winner.get("metrics", {}),
        },
        "policy_snapshot": {
            "bundle_id": bundle.get("bundle_id"),
            "source_run_id": bundle_source_run_id,
            "bundle_mode": bundle.get("bundle_mode"),
            "policy_type": strategy.get("policy_type"),
            "strategy_id": strategy.get("strategy_id"),
            "symbol_scope_count": len(strategy.get("symbol_scope", [])),
            "allow_if": strategy.get("decision_rules", {}).get("allow_if", []),
            "reject_if": strategy.get("decision_rules", {}).get("reject_if", []),
            "boost_score": strategy.get("decision_rules", {}).get("boost_score"),
            "valid_until": strategy.get("valid_until"),
        },
        "manual_brief": manual_brief_payload["manual_brief"],
        "snapshot_metadata": snapshot_metadata,
        "policy_materiality": policy_materiality,
        "warnings": warnings,
    }


def render_text_summary(payload: dict[str, Any]) -> str:
    strategy = payload["strategy_snapshot"]
    policy = payload["policy_snapshot"]
    brief = payload["manual_brief"]
    snapshot_metadata = payload.get("snapshot_metadata", {})
    materiality = payload.get("policy_materiality", {})
    sources = payload.get("sources", {})
    metrics = strategy.get("metrics", {})
    summary = brief.get("summary", {})
    market_filter = snapshot_metadata.get("market_filter", {}) if isinstance(snapshot_metadata, dict) else {}
    counterfactual_buys = snapshot_metadata.get("counterfactual_buys_without_market_filter", []) if isinstance(snapshot_metadata, dict) else []

    lines = [
        f"generated_at: {payload.get('generated_at', '-')}",
        "",
        "strategy:",
        f"- strategy_id: {strategy.get('strategy_id', '-')}",
        f"- source_run_id: {strategy.get('source_run_id', '-')}",
        f"- symbol: {strategy.get('symbol', '-')}",
        f"- timeframe: {strategy.get('timeframe', '-')}",
        f"- sharpe: {metrics.get('sharpe', '-')}",
        f"- max_drawdown: {metrics.get('max_drawdown', '-')}",
        f"- win_rate: {metrics.get('win_rate', '-')}",
        f"- trades: {metrics.get('trades', '-')}",
        f"- cagr: {metrics.get('cagr', '-')}",
        "",
        "policy:",
        f"- bundle_id: {policy.get('bundle_id', '-')}",
        f"- mode: {policy.get('bundle_mode', '-')}",
        f"- policy_type: {policy.get('policy_type', '-')}",
        f"- symbol_scope_count: {policy.get('symbol_scope_count', 0)}",
        f"- boost_score: {policy.get('boost_score', '-')}",
        f"- valid_until: {policy.get('valid_until', '-')}",
        "",
        "sources:",
        f"- approved_strategy: {sources.get('approved_strategy_path', '-')}",
        f"- policy_bundle: {sources.get('policy_bundle_path', '-')}",
        f"- manual_brief: {sources.get('manual_brief_source', '-')}",
        f"- brief_source_kind: {sources.get('manual_brief_source_kind', '-')}",
        f"- brief_mtime_utc: {sources.get('manual_brief_mtime_utc', '-')}",
        "",
        "market_filter:",
        f"- active: {bool(market_filter.get('below_ema', False))}",
        f"- symbol: {market_filter.get('symbol', '-')}",
        f"- close: {market_filter.get('close', '-')}",
        f"- ema_period: {market_filter.get('ema_period', '-')}",
        f"- ema: {market_filter.get('ema', '-')}",
        "",
        "policy_materiality:",
        f"- boosted_candidates: {materiality.get('boosted_candidate_count', 0)}",
        f"- direct_reversals: {materiality.get('direct_reversal_count', 0)}",
        f"- near_misses: {materiality.get('near_miss_count', 0)}",
        f"- cutoff_rank: {materiality.get('cutoff_rank', '-')}",
        f"- cutoff_score: {materiality.get('cutoff_score', '-')}",
        "",
        "manual_brief:",
        f"- headline: {brief.get('headline', '-')}",
        f"- BUY: {int(summary.get('buy_count', 0))}",
        f"- HOLD: {int(summary.get('hold_count', 0))}",
        f"- NO_BUY: {int(summary.get('no_buy_count', 0))}",
        f"- policy_reversal: {int(summary.get('scheduled_due_to_policy_count', 0))}",
        f"- near_miss_after_policy: {int(summary.get('near_miss_after_policy_count', 0))}",
        "",
        "watchlist:",
    ]
    for row in brief.get("watchlist", []):
        lines.append(
            "  "
            + " | ".join(
                [
                    str(row.get("symbol", "-")),
                    f"action={row.get('action', '-')}",
                    f"rank={row.get('rank', '-')}",
                    f"decision={row.get('final_decision', '-')}",
                    f"policy={row.get('policy_materiality', '-')}",
                ]
            )
        )
        lines.append(f"    note: {row.get('action_reason', '-')}")

    if counterfactual_buys:
        lines.extend(["", "counterfactual_buys_without_market_filter:"])
        for row in counterfactual_buys:
            lines.append(
                "  "
                + " | ".join(
                    [
                        str(row.get("symbol", "-")),
                        f"rank={row.get('final_rank', '-')}",
                        f"score={row.get('final_ranking_score', '-')}",
                        f"policy={row.get('policy_materiality', '-')}",
                        f"decision={row.get('policy_decision', '-')}",
                    ]
                )
            )

    closest_to_reversal = materiality.get("closest_to_reversal", [])
    if closest_to_reversal:
        lines.extend(["", "closest_boosted_candidates_to_reversal:"])
        for row in closest_to_reversal:
            lines.append(
                "  "
                + " | ".join(
                    [
                        str(row.get("symbol", "-")),
                        f"raw_rank={row.get('raw_rank', '-')}",
                        f"final_rank={row.get('final_rank', '-')}",
                        f"delta={row.get('applied_delta', '-')}",
                        f"gap_after_boost={row.get('gap_to_cutoff_after_boost', '-')}",
                        f"extra_delta_needed={row.get('required_extra_delta_for_cutoff', '-')}",
                        f"policy={row.get('policy_materiality', '-')}",
                    ]
                )
            )

    if payload.get("warnings"):
        lines.extend(["", "warnings:"])
        for warning in payload["warnings"]:
            lines.append(f"- {warning}")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a manual trading daily summary from local artifacts.")
    parser.add_argument("--run-id", default=None, help="Optional run_id for selecting a specific hourly brief")
    parser.add_argument("--artifacts-dir", default="artifacts")
    parser.add_argument("--reexport-dir", default="artifacts_reexport")
    parser.add_argument("--logs-dir", default="logs")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    payload = build_manual_daily_summary(
        artifacts_dir=Path(args.artifacts_dir),
        reexport_dir=Path(args.reexport_dir),
        logs_dir=Path(args.logs_dir),
        run_id=args.run_id,
    )
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_text_summary(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
