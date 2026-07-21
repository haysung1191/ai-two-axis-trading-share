from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.domains.governance.contracts import ApprovedStrategyBundle
from jobs.hourly_job import _attach_candidate_attribution, _capped_policy_delta, _effective_score
from src.config import AppConfig, load_config
from src.data.bithumb_client import BithumbPublicClient
from src.manual.briefing import build_hourly_manual_brief
from src.manual.recommendations import build_manual_trade_recommendation
from src.policy.loader import PolicyBundleLoader
from src.policy.models import PolicyCandidateInput, PolicyFlags, PolicyRuntimeState
from src.policy.normalization import normalize_candidate_features
from src.policy.runtime import evaluate_policy_candidates, read_policy_flags
from src.scanner.scanner import Candidate, scan_symbol
from src.timeutil import iso_utc, latest_closed_candle_close_ts_ms, now_utc_ms, run_id_for_close_ts


def _find_latest(root: Path, relative_parts: list[str]) -> Path:
    matches = sorted(root.rglob(relative_parts[-1]), key=lambda path: path.stat().st_mtime, reverse=True)
    for path in matches:
        if list(path.parts[-len(relative_parts):]) == relative_parts:
            return path
    raise FileNotFoundError(f"Could not find {'/'.join(relative_parts)} under {root}")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid JSON payload: {path}")
    return payload


def _read_snapshot_policy_flags() -> PolicyFlags:
    return read_policy_flags()


def _load_latest_policy_state(reexport_dir: Path):
    bundle_path = _find_latest(reexport_dir, ["publish", "policy_bundle.json"])
    manifest_path = _find_latest(reexport_dir, ["publish", "manifest.json"])
    flags = _read_snapshot_policy_flags()
    state = PolicyBundleLoader(str(bundle_path), str(manifest_path)).load(flags)
    return flags, state, bundle_path, manifest_path


def _load_latest_approved_bundle(artifacts_dir: Path) -> tuple[ApprovedStrategyBundle, Path]:
    approved_path = _find_latest(artifacts_dir, ["approved_strategy.json"])
    payload = _load_json(approved_path)
    return ApprovedStrategyBundle.model_validate(payload), approved_path


def _market_downtrend(symbol_rows: dict[str, list[tuple[int, float, float, float, float, float]]], *, close_ts_ms: int, interval_ms: int, cfg: AppConfig) -> bool:
    diagnostics = _market_filter_diagnostics(symbol_rows, close_ts_ms=close_ts_ms, interval_ms=interval_ms, cfg=cfg)
    if not diagnostics.get("available", False):
        return True
    if diagnostics.get("ema") is None:
        return True
    return bool(diagnostics.get("below_ema"))


def _market_filter_diagnostics(
    symbol_rows: dict[str, list[tuple[int, float, float, float, float, float]]],
    *,
    close_ts_ms: int,
    interval_ms: int,
    cfg: AppConfig,
) -> dict[str, Any]:
    market_sym = str(cfg.strategy.get("market_filter_symbol", "BTC"))
    rows = symbol_rows.get(market_sym)
    if not rows:
        return {
            "symbol": market_sym,
            "available": False,
            "ema_period": int(cfg.strategy.get("market_filter_ema", 26)),
            "below_ema": True,
            "fail_closed": True,
            "failure_reason": "market_filter_symbol_missing",
        }

    signal_start_ts_ms = int(close_ts_ms - interval_ms)
    by_ts = {int(ts): float(c) for ts, o, h, l, c, v in rows}
    keys = sorted(k for k in by_ts.keys() if k <= signal_start_ts_ms)
    period = int(cfg.strategy.get("market_filter_ema", 26))
    if len(keys) < period:
        return {
            "symbol": market_sym,
            "available": True,
            "ema_period": period,
            "signal_start_ts_ms": signal_start_ts_ms,
            "sample_count": len(keys),
            "below_ema": True,
            "fail_closed": True,
            "failure_reason": "insufficient_market_filter_history",
        }

    closes = [by_ts[k] for k in keys]
    from src.scanner.indicators import ema

    ema_v = ema(closes, period)
    last_close = closes[-1]
    last_ema = float(ema_v[-1]) if ema_v else None
    return {
        "symbol": market_sym,
        "available": True,
        "ema_period": period,
        "signal_start_ts_ms": signal_start_ts_ms,
        "sample_count": len(keys),
        "close": last_close,
        "ema": last_ema,
        "below_ema": bool(last_ema is not None and last_close < last_ema),
        "fail_closed": bool(last_ema is None),
        "failure_reason": "ema_unavailable" if last_ema is None else None,
    }


def _fetch_candidates(*, cfg: AppConfig, close_ts_ms: int, client: BithumbPublicClient) -> tuple[list[Candidate], dict[str, list[tuple[int, float, float, float, float, float]]]]:
    interval_ms = int(cfg.strategy.get("interval_ms", 3600000))
    market_filter_symbol = str(cfg.strategy.get("market_filter_symbol", "BTC"))
    tickers = client.list_krw_tickers_by_quote_volume(
        min_quote_krw_24h=float(cfg.exchange.get("krw_quote_volume_24h_min", 300_000_000)),
        max_symbols=int(cfg.exchange.get("max_symbols", 120)),
    )
    symbol_rows: dict[str, list[tuple[int, float, float, float, float, float]]] = {}
    candidates: list[Candidate] = []

    for ticker in tickers:
        rows = client.fetch_1h_candles(ticker.symbol)
        if not rows:
            continue
        symbol_rows[ticker.symbol] = rows
        candidate = scan_symbol(
            ticker.symbol,
            close_ts_ms,
            interval_ms,
            rows,
            cfg.scanner,
            cfg.strategy,
        )
        if candidate is not None:
            candidates.append(candidate)

    if market_filter_symbol not in symbol_rows:
        try:
            rows = client.fetch_1h_candles(market_filter_symbol)
        except Exception:
            rows = []
        if rows:
            symbol_rows[market_filter_symbol] = rows
    return candidates, symbol_rows


def _build_snapshot_payload(
    *,
    cfg: AppConfig,
    close_ts_ms: int,
    run_id: str,
    candidates: list[Candidate],
    policy_flags: PolicyFlags,
    policy_state: Any,
    approved_bundle: ApprovedStrategyBundle,
    approved_path: Path,
    bundle_path: Path,
    manifest_path: Path,
    market_downtrend: bool,
    market_filter_diagnostics: dict[str, Any],
    top_n: int,
    trace_count: int,
) -> dict[str, Any]:
    policy_inputs = [
        PolicyCandidateInput(
            symbol=f"KRW-{candidate.symbol}",
            scanner_score=float(candidate.score),
            features=normalize_candidate_features(candidate),
        )
        for candidate in candidates
    ]
    policy_results = evaluate_policy_candidates(
        ts_ms=close_ts_ms,
        candidates=policy_inputs,
        flags=policy_flags,
        runtime_state=policy_state,
    )

    final_ranked_candidates = sorted(
        candidates,
        key=lambda item: (-_effective_score(item.symbol, float(item.score), policy_results, policy_flags), item.symbol),
    )
    raw_ranked_candidates = sorted(candidates, key=lambda item: (-float(item.score), item.symbol))
    traced_candidates = final_ranked_candidates[: max(1, top_n, trace_count)]

    candidate_trace_context: dict[str, dict[str, Any]] = {}
    outcomes: dict[str, dict[str, Any]] = {}
    for candidate in traced_candidates:
        policy_result = policy_results.get(f"KRW-{candidate.symbol}")
        raw_delta = float(policy_result.policy_score_delta) if policy_result else 0.0
        capped_delta = _capped_policy_delta(policy_result, policy_flags)
        adjusted_score = _effective_score(candidate.symbol, float(candidate.score), policy_results, policy_flags)
        candidate_trace_context[candidate.symbol] = {
            "scanner_score_before_policy": float(candidate.score),
            "final_ranking_score": adjusted_score,
            "normalized_feature_snapshot": normalize_candidate_features(candidate),
            "suggested_stop_dist": float(candidate.stop_dist),
            "suggested_tp_dist": float(candidate.tp_dist),
            "suggested_time_exit_ts_ms": int(candidate.time_exit_ts_ms),
            "policy_result": {
                "matched_strategy_id": policy_result.matched_strategy_id if policy_result else None,
                "policy_decision": policy_result.policy_decision if policy_result else "NEUTRAL",
                "policy_score_delta_raw": raw_delta,
                "policy_score_delta_capped": capped_delta,
                "reasons": list(policy_result.reasons) if policy_result else [],
                "deterministic_hash": policy_result.deterministic_hash if policy_result else None,
            },
        }
        blocked_reason = None
        if policy_result is not None and policy_result.policy_decision == "SOFT_REJECT" and policy_flags.soft_reject_enabled:
            blocked_reason = "POLICY_SOFT_REJECT"
        elif market_downtrend:
            blocked_reason = "MARKET_DOWNTREND"
        elif final_ranked_candidates.index(candidate) >= top_n:
            blocked_reason = "BELOW_ENTRY_CUTOFF"
        outcomes[candidate.symbol] = {"blocked_reason": blocked_reason}

    _attach_candidate_attribution(
        traced_candidates=traced_candidates,
        final_candidates=final_ranked_candidates,
        raw_candidates=raw_ranked_candidates,
        trace_context=candidate_trace_context,
        outcomes=outcomes,
    )

    recommendations: list[dict[str, Any]] = []
    signals: list[dict[str, Any]] = []
    for candidate in traced_candidates:
        trace_ctx = candidate_trace_context[candidate.symbol]
        blocked_reason = outcomes[candidate.symbol]["blocked_reason"]
        recommendation = build_manual_trade_recommendation(
            symbol=candidate.symbol,
            blocked_reason=blocked_reason,
            trace_ctx=trace_ctx,
        )
        recommendation.update(
            {
                "rank": trace_ctx.get("final_rank"),
                "final_ranking_score": trace_ctx.get("final_ranking_score"),
                "scanner_score_before_policy": trace_ctx.get("scanner_score_before_policy"),
                "final_decision": "SCHEDULED" if blocked_reason is None else f"CANCELED:{blocked_reason}",
                "scheduled_due_to_policy": bool(trace_ctx.get("scheduled_due_to_policy")),
                "near_miss_after_policy": bool(trace_ctx.get("near_miss_after_policy")),
                "blocked_reason": blocked_reason,
                "raw_rank": trace_ctx.get("raw_rank"),
                "final_rank": trace_ctx.get("final_rank"),
                "entry_cutoff_rank": trace_ctx.get("entry_cutoff_rank"),
                "cutoff_score_raw": trace_ctx.get("cutoff_score_raw"),
                "cutoff_score_final": trace_ctx.get("cutoff_score_final"),
                "would_have_been_scheduled_without_policy": trace_ctx.get("would_have_been_scheduled_without_policy"),
                "shortfall_after_policy": trace_ctx.get("shortfall_after_policy"),
            }
        )
        recommendations.append(recommendation)
        signals.append(
            {
                "symbol": candidate.symbol,
                "score": float(trace_ctx["final_ranking_score"]),
                "rank": int(trace_ctx["final_rank"]),
                "blocked_reason": blocked_reason,
                "raw_rank": trace_ctx.get("raw_rank"),
                "final_rank": trace_ctx.get("final_rank"),
                "entry_cutoff_rank": trace_ctx.get("entry_cutoff_rank"),
                "cutoff_score_raw": trace_ctx.get("cutoff_score_raw"),
                "cutoff_score_final": trace_ctx.get("cutoff_score_final"),
                "would_have_been_scheduled_without_policy": trace_ctx.get("would_have_been_scheduled_without_policy"),
                "scheduled_due_to_policy": trace_ctx.get("scheduled_due_to_policy"),
                "near_miss_after_policy": trace_ctx.get("near_miss_after_policy"),
                "shortfall_after_policy": trace_ctx.get("shortfall_after_policy"),
            }
        )

    counterfactual_buys_without_market_filter: list[dict[str, Any]] = []
    if market_downtrend:
        for candidate in final_ranked_candidates[: max(1, top_n)]:
            trace_ctx = candidate_trace_context.get(candidate.symbol)
            if trace_ctx is None:
                continue
            recommendation = build_manual_trade_recommendation(
                symbol=candidate.symbol,
                blocked_reason=None,
                trace_ctx=trace_ctx,
            )
            counterfactual_buys_without_market_filter.append(
                {
                    "symbol": candidate.symbol,
                    "final_rank": trace_ctx.get("final_rank"),
                    "final_ranking_score": trace_ctx.get("final_ranking_score"),
                    "policy_materiality": recommendation.get("policy_materiality"),
                    "policy_decision": recommendation.get("policy_decision"),
                    "reference_price_krw": recommendation.get("reference_price_krw"),
                }
            )

    manual_brief = build_hourly_manual_brief(
        run_id=run_id,
        candle_close_utc=iso_utc(close_ts_ms),
        signals=recommendations,
    )
    approved_winner = approved_bundle.winners[0] if approved_bundle.winners else None
    return {
        "run_id": run_id,
        "candle_close_utc": iso_utc(close_ts_ms),
        "snapshot_mode": "read_only_manual_snapshot",
        "manual_brief": manual_brief,
        "manual_recommendations": recommendations,
        "signals": signals,
        "metadata": {
            "generated_at": datetime.now(tz=UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "approved_strategy_path": str(approved_path),
            "policy_bundle_path": str(bundle_path),
            "policy_manifest_path": str(manifest_path),
            "approved_strategy_id": approved_winner.strategy_id if approved_winner else None,
            "policy_bundle_id": policy_state.bundle.bundle_id if policy_state.bundle else None,
            "market_downtrend": market_downtrend,
            "market_filter": market_filter_diagnostics,
            "counterfactual_buys_without_market_filter": counterfactual_buys_without_market_filter,
            "candidate_count": len(candidates),
            "traced_candidate_count": len(traced_candidates),
            "top_n": top_n,
            "policy_flags": asdict(policy_flags),
        },
    }


def generate_manual_snapshot(
    *,
    artifacts_dir: Path,
    reexport_dir: Path,
    logs_dir: Path,
    trace_count: int = 15,
    allow_policy_fallback: bool = False,
) -> Path:
    cfg = load_config()
    interval_ms = int(cfg.strategy.get("interval_ms", 3600000))
    close_ts_ms = latest_closed_candle_close_ts_ms(now_utc_ms(), interval_ms)
    run_id = run_id_for_close_ts(close_ts_ms)

    policy_flags, policy_state, bundle_path, manifest_path = _load_latest_policy_state(reexport_dir)
    if policy_state.bundle is None:
        detail = f"{policy_state.status} {policy_state.error or ''}".strip()
        if not allow_policy_fallback:
            raise RuntimeError(
                "Policy bundle is not loadable for manual snapshot generation: "
                f"{detail}. Set the local policy env flags to the intended runtime mode before generating a snapshot."
            )
        policy_flags = PolicyFlags()
        policy_state = PolicyRuntimeState(
            status=f"fallback_from_{policy_state.status}",
            bundle=None,
            manifest=policy_state.manifest,
            error=policy_state.error,
        )

    approved_bundle, approved_path = _load_latest_approved_bundle(artifacts_dir)

    client = BithumbPublicClient()
    try:
        candidates, symbol_rows = _fetch_candidates(cfg=cfg, close_ts_ms=close_ts_ms, client=client)
    finally:
        client.close()

    if not candidates:
        raise RuntimeError("No scanner candidates were produced for the latest closed candle.")

    payload = _build_snapshot_payload(
        cfg=cfg,
        close_ts_ms=close_ts_ms,
        run_id=run_id,
        candidates=candidates,
        policy_flags=policy_flags,
        policy_state=policy_state,
        approved_bundle=approved_bundle,
        approved_path=approved_path,
        bundle_path=bundle_path,
        manifest_path=manifest_path,
        market_downtrend=_market_downtrend(symbol_rows, close_ts_ms=close_ts_ms, interval_ms=interval_ms, cfg=cfg),
        market_filter_diagnostics=_market_filter_diagnostics(symbol_rows, close_ts_ms=close_ts_ms, interval_ms=interval_ms, cfg=cfg),
        top_n=int(cfg.scanner.get("top_n", 10)),
        trace_count=max(1, trace_count),
    )

    logs_dir.mkdir(parents=True, exist_ok=True)
    out_path = logs_dir / f"manual_snapshot_{run_id.replace(':', '_')}.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a fresh read-only manual trading snapshot from live Bithumb market data.")
    parser.add_argument("--artifacts-dir", default="artifacts")
    parser.add_argument("--reexport-dir", default="artifacts_reexport")
    parser.add_argument("--logs-dir", default="logs")
    parser.add_argument("--trace-count", type=int, default=15)
    parser.add_argument(
        "--allow-policy-fallback",
        action="store_true",
        help=(
            "Generate a read-only baseline scanner snapshot when the policy bundle is disabled, "
            "missing, expired, or invalid. This does not enable policy enforcement or live trading."
        ),
    )
    args = parser.parse_args()

    out_path = generate_manual_snapshot(
        artifacts_dir=Path(args.artifacts_dir),
        reexport_dir=Path(args.reexport_dir),
        logs_dir=Path(args.logs_dir),
        trace_count=max(1, args.trace_count),
        allow_policy_fallback=bool(args.allow_policy_fallback),
    )
    print(json.dumps({"snapshot_path": str(out_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
