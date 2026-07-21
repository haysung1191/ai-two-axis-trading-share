from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
OUT_JSON = ROOT / "reports" / "operations" / "two_axis_model_inventory_latest.json"
OUT_MD = ROOT / "reports" / "operations" / "two_axis_model_inventory_latest.md"


def read_json(rel_path: str) -> Any:
    path = ROOT / rel_path
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def maybe_read_json(rel_path: str) -> Any | None:
    path = ROOT / rel_path
    if not path.exists():
        return None
    return read_json(rel_path)


def metric(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def pct(value: Any) -> str:
    if value is None:
        return "n/a"
    return f"{float(value) * 100:.2f}%"


def candidate_id(item: dict[str, Any]) -> str:
    return str(item.get("candidate_id") or item.get("family") or item.get("experiment_id") or "unknown")


def top_rows(rows: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    return rows[:limit]


def oos_candidate_summary(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        return {}
    summary = row.get("summary") or row.get("aggregate") or {}
    conversion = row.get("conversion") or row.get("source_conversion") or {}
    return {
        "candidate_id": row.get("candidate_id"),
        "status": row.get("status"),
        "market": row.get("market"),
        "estimated_cagr": conversion.get("estimated_cagr"),
        "estimated_mdd": conversion.get("estimated_mdd"),
        "source_cagr": conversion.get("source_cagr"),
        "source_mdd": conversion.get("source_mdd"),
        "source_profit_factor": conversion.get("source_profit_factor"),
        "average_fold_cagr": summary.get("average_fold_cagr"),
        "worst_fold_mdd": summary.get("worst_fold_mdd"),
        "total_trade_count": summary.get("total_trade_count"),
    }


def find_candidate(rows: list[dict[str, Any]], candidate: str | None) -> dict[str, Any] | None:
    if not candidate:
        return None
    return next((row for row in rows if row.get("candidate_id") == candidate), None)


def signal_selection_summary(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        return {}
    return {
        "candidate_id": row.get("candidate_id"),
        "selection_rank": row.get("selection_rank"),
        "selection_key": row.get("selection_key"),
        "estimated_cagr": ((row.get("selection_key") or {}).get("estimated_cagr")),
        "pass_fold_count": ((row.get("selection_key") or {}).get("pass_fold_count")),
        "average_fold_cagr": ((row.get("selection_key") or {}).get("average_fold_cagr")),
        "total_trade_count": ((row.get("selection_key") or {}).get("total_trade_count")),
    }


def signal_gap_summary(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        return {}
    signal = row.get("signal") or {}
    gap = row.get("signal_gap") or {}
    return {
        "candidate_id": row.get("candidate_id"),
        "market": row.get("market"),
        "near_miss_rank": row.get("near_miss_rank"),
        "momentum": signal.get("momentum"),
        "momentum_threshold": signal.get("momentum_threshold"),
        "volume_ratio": signal.get("volume_ratio"),
        "volume_ratio_floor": signal.get("volume_ratio_floor"),
        "momentum_gap": gap.get("momentum_gap"),
        "volume_gap": gap.get("volume_gap"),
        "nearest_trigger_gap": gap.get("nearest_trigger_gap"),
        "blocking_conditions": gap.get("blocking_conditions", []),
    }


def summarize_bithumb() -> dict[str, Any]:
    verified = read_json("reports/operations/bithumb_verified_crypto_model_factory_latest.json")
    long_history = read_json("reports/operations/bithumb_verified_crypto_model_factory_longhistory_latest.json")
    scout = read_json("reports/operations/bithumb_current_actionable_nonzero_signal_scout_latest.json")
    direct = read_json("reports/model_factory/two_axis_direct_model_development_latest.json")
    oos = read_json("reports/model_factory/bithumb_current_actionable_oos_walkforward_latest.json")
    stress = read_json("reports/model_factory/bithumb_current_actionable_robustness_stress_latest.json")
    sweep = read_json("reports/model_factory/bithumb_current_actionable_parameter_sweep_latest.json")
    conversion = read_json("reports/model_factory/bithumb_current_actionable_risk_conversion_latest.json")

    latest_leaderboard = verified.get("leaderboard", [])
    long_leaderboard = long_history.get("leaderboard", [])
    sweeps = sweep.get("sweeps", [])
    conversions = conversion.get("conversions", [])
    evaluations = oos.get("evaluations", [])
    triggered = scout.get("triggered_candidates", [])
    top_signal = scout.get("top_triggered_candidate") or {}
    top_near_miss = scout.get("top_near_miss") or scout.get("top_near_miss_candidate") or {}
    top_near_miss_candidates = scout.get("top_near_miss_candidates") or ([top_near_miss] if top_near_miss else [])
    oos_top = oos.get("top_oos") or {}
    top_signal_oos = find_candidate(evaluations, top_signal.get("candidate_id"))
    top_oos_eval = find_candidate(evaluations, oos_top.get("candidate_id")) or oos_top
    oos_top_triggered = find_candidate(triggered, oos_top.get("candidate_id"))

    status_counts = Counter(str(row.get("status", "unknown")) for row in sweeps)
    conversion_status_counts = Counter(str(row.get("status", "unknown")) for row in conversions)
    oos_status_counts = Counter(str(row.get("status", "unknown")) for row in evaluations)

    return {
        "axis": "BITHUMB_KRW",
        "evidence_files": [
            "reports/operations/bithumb_verified_crypto_model_factory_latest.json",
            "reports/operations/bithumb_verified_crypto_model_factory_longhistory_latest.json",
            "reports/operations/bithumb_current_actionable_nonzero_signal_scout_latest.json",
            "reports/model_factory/bithumb_current_actionable_parameter_sweep_latest.json",
            "reports/model_factory/bithumb_current_actionable_risk_conversion_latest.json",
            "reports/model_factory/bithumb_current_actionable_oos_walkforward_latest.json",
            "reports/model_factory/bithumb_current_actionable_robustness_stress_latest.json",
            "reports/model_factory/two_axis_direct_model_development_latest.json",
        ],
        "universe": {
            "ready_market_count": verified.get("data", {}).get("ready_market_count"),
            "selected_market_count": verified.get("data", {}).get("selected_market_count"),
            "long_history_universes": long_history.get("universes", {}),
        },
        "counts": {
            "latest_verified_leaderboard_models": len(latest_leaderboard),
            "long_history_leaderboard_models": len(long_leaderboard),
            "long_history_research_watchlist_models": len(long_history.get("research_watchlist", [])),
            "current_actionable_parameter_sweeps": len(sweeps),
            "current_actionable_risk_conversions": len(conversions),
            "current_actionable_oos_evaluations": len(evaluations),
            "current_actionable_oos_pass": oos.get("aggregate", {}).get("pass_count"),
            "current_nonzero_signal_candidates": len(triggered),
        },
        "status_counts": {
            "sweep": dict(status_counts),
            "conversion": dict(conversion_status_counts),
            "oos": dict(oos_status_counts),
        },
        "leaders": {
            "verified_latest_top": [
                {
                    "id": candidate_id(row),
                    "cagr": row.get("total", {}).get("cagr"),
                    "mdd": row.get("total", {}).get("mdd"),
                    "sharpe": row.get("total", {}).get("sharpe"),
                    "test_cagr": row.get("test", {}).get("cagr"),
                    "source": "bithumb_verified_crypto_model_factory_latest",
                }
                for row in top_rows(latest_leaderboard)
            ],
            "long_history_top": [
                {
                    "id": candidate_id(row),
                    "universe": row.get("universe"),
                    "cagr": row.get("total", {}).get("cagr"),
                    "mdd": row.get("total", {}).get("mdd"),
                    "sharpe": row.get("total", {}).get("sharpe"),
                    "test_cagr": row.get("test", {}).get("cagr"),
                    "source": "bithumb_verified_crypto_model_factory_longhistory",
                }
                for row in top_rows(long_leaderboard)
            ],
            "current_actionable_top_sweep": sweep.get("top_sweep"),
            "current_actionable_top_conversion": conversion.get("top_conversion"),
            "current_actionable_top_signal": top_signal,
        },
        "verification_sources": {
            "current_signal_generated_at": scout.get("generated_at") or scout.get("generated_at_utc"),
            "current_signal_generated_at_utc": scout.get("generated_at_utc"),
            "current_signal_evaluated_count": scout.get("evaluated_count") or scout.get("evaluated_candidate_count"),
            "current_signal_triggered_count": scout.get("triggered_count") or scout.get("triggered_candidate_count"),
            "oos_generated_at": oos.get("generated_at") or oos.get("generated_at_utc"),
            "oos_top_candidate_id": oos_top.get("candidate_id"),
            "oos_top_market": oos_top.get("market"),
            "current_signal_candidate_id": top_signal.get("candidate_id"),
            "current_signal_matches_oos_top": (
                top_signal.get("candidate_id") == oos_top.get("candidate_id")
                if top_signal.get("candidate_id") and oos_top.get("candidate_id")
                else None
            ),
            "current_signal_selection_policy": scout.get("selection_policy"),
            "current_signal_selection_summary": signal_selection_summary(top_signal),
            "oos_top_signal_selection_summary": signal_selection_summary(oos_top_triggered),
            "current_signal_top_near_miss": signal_gap_summary(top_near_miss),
            "current_signal_top_near_miss_candidates": [
                signal_gap_summary(row)
                for row in top_rows(top_near_miss_candidates)
            ],
            "current_signal_oos_summary": oos_candidate_summary(top_signal_oos),
            "oos_top_summary": oos_candidate_summary(top_oos_eval),
            "robustness_generated_at": stress.get("generated_at") or stress.get("generated_at_utc"),
            "robustness_candidate_id": stress.get("candidate_id"),
            "robustness_source_oos": stress.get("source_oos"),
            "direct_generated_at_utc": direct.get("generated_at_utc"),
            "direct_crypto_candidate_count": (direct.get("crypto") or {}).get("candidate_count"),
            "direct_crypto_oos_pass_count": (direct.get("crypto") or {}).get("oos_pass_count"),
            "direct_crypto_validated_pass_count": (direct.get("crypto") or {}).get("validated_pass_count"),
            "direct_crypto_archive_signal_triggered_count": (direct.get("crypto") or {}).get("archive_signal_triggered_count"),
            "direct_crypto_top_live_signal_triggered_count": (direct.get("crypto") or {}).get("top_live_signal_triggered_count"),
            "direct_crypto_top_live_signal_all_verified": ((direct.get("crypto") or {}).get("top_live_signal_summary") or {}).get("all_live_verified"),
            "direct_crypto_top_live_near_miss_candidate": (direct.get("crypto") or {}).get("top_live_near_miss_candidate"),
        },
    }


def summarize_kis() -> dict[str, Any]:
    registry = read_json("reports/operations/verified_candidate_registry/verified_candidate_registry_latest.json")
    stock_queue = read_json("reports/model_factory/stock_risk_conversion_queue_latest.json")
    stock_packet = read_json("reports/model_factory/stock_conversion_gatekeeper_review_packet_latest.json")
    experiment_queue = read_json("reports/model_factory/model_factory_experiment_queue_latest.json")
    direct = read_json("reports/model_factory/two_axis_direct_model_development_latest.json")
    bridge = read_json("ops/stock_etf_operating_candidate_bridge/stock_etf_operating_candidate_bridge_latest.json")
    latest = maybe_read_json("overnight_runs/latest_run_summary.json") or {}

    candidates = registry.get("candidates", [])
    axis_counts = Counter(str(row.get("axis", "unknown")) for row in candidates)
    stock_candidates = [
        row
        for row in candidates
        if "stock" in str(row.get("axis", "")).lower()
        or "etf" in str(row.get("axis", "")).lower()
        or "kis" in str(row.get("axis", "")).lower()
    ]
    stock_queue_rows = stock_queue.get("queue", [])
    experiment_rows = experiment_queue.get("queue", [])
    lane_counts = experiment_queue.get("summary", {}).get("lane_counts", {})
    direct_top_variant = ((direct.get("kis") or {}).get("top_variants") or [{}])[0]
    direct_top_parent_candidate_id = direct_top_variant.get("parent_candidate_id")

    return {
        "axis": "KIS_COMBINED_KRW",
        "evidence_files": [
            "reports/operations/verified_candidate_registry/verified_candidate_registry_latest.json",
            "reports/model_factory/stock_risk_conversion_queue_latest.json",
            "reports/model_factory/stock_conversion_gatekeeper_review_packet_latest.json",
            "reports/model_factory/model_factory_experiment_queue_latest.json",
            "reports/model_factory/two_axis_direct_model_development_latest.json",
            "ops/stock_etf_operating_candidate_bridge/stock_etf_operating_candidate_bridge_latest.json",
            "overnight_runs/latest_run_summary.json",
        ],
        "universe": {
            "stock_etf_loaded_symbols": registry.get("summary", {}).get("stock_etf_loaded_symbols"),
            "fx_mode": registry.get("summary", {}).get("stock_etf_fx_mode"),
            "data_guard_status": registry.get("verified_data_guard", {}).get("status"),
        },
        "counts": {
            "verified_registry_candidates_all_axes": len(candidates),
            "verified_registry_stock_etf_candidates": len(stock_candidates),
            "stock_risk_conversion_queue": len(stock_queue_rows),
            "stock_risk_conversion_ready": stock_queue.get("ready_candidate_count"),
            "stock_risk_conversion_blocked": stock_queue.get("blocked_candidate_count"),
            "model_factory_experiment_queue": len(experiment_rows),
            "model_factory_ready_experiments": experiment_queue.get("summary", {}).get("ready_experiment_count"),
            "model_factory_waiting_for_human_review": experiment_queue.get("summary", {}).get("waiting_for_human_review_count"),
        },
        "axis_counts_in_registry": dict(axis_counts),
        "lane_counts_in_experiment_queue": lane_counts,
        "leaders": {
            "stock_risk_conversion_top": [
                {
                    "id": row.get("candidate_id"),
                    "lane": row.get("lane"),
                    "status": row.get("status"),
                    "before_cagr": row.get("before", {}).get("cagr"),
                    "before_mdd": row.get("before", {}).get("mdd"),
                    "estimated_cagr": row.get("proposed_conversion", {}).get("estimated_cagr"),
                    "estimated_mdd": row.get("proposed_conversion", {}).get("estimated_mdd"),
                    "overlay": row.get("proposed_conversion", {}).get("overlay"),
                }
                for row in top_rows(stock_queue_rows)
            ],
            "gatekeeper_review_candidate": {
                "id": stock_packet.get("candidate_id"),
                "before": stock_packet.get("before"),
                "proposed_conversion": stock_packet.get("proposed_conversion"),
                "readiness_checks": stock_packet.get("readiness_checks"),
            },
            "latest_summary_stock": latest.get("stock"),
        },
        "verification_sources": {
            "direct_generated_at_utc": direct.get("generated_at_utc"),
            "direct_source_bridge": (direct.get("kis") or {}).get("source_bridge"),
            "direct_universe_validation_mode": (direct.get("kis") or {}).get("universe_validation_mode"),
            "direct_top_parent_candidate_id": direct_top_parent_candidate_id,
            "bridge_generated_at_utc": bridge.get("generated_at_utc"),
            "bridge_candidate_id": bridge.get("candidate_id"),
            "bridge_matches_direct_top_parent": (
                bridge.get("candidate_id") == direct_top_parent_candidate_id
                if bridge.get("candidate_id") and direct_top_parent_candidate_id
                else None
            ),
            "bridge_universe_validation_mode": bridge.get("universe_validation_mode"),
            "bridge_universe_validation_verifier_status": bridge.get("universe_validation_verifier_status"),
        },
    }


def summarize_safety() -> dict[str, Any]:
    stage13 = maybe_read_json("reports/operations/stage13_completion_audit_latest.json") or {}
    intent = maybe_read_json("reports/operations/tiny_live_order_intent_pretrade_latest.json") or {}
    disable_path = ROOT / "ops" / "runstate" / "DISABLE_ALL_TRADING"
    raw_stage13_decision = stage13.get("completion_decision", {})
    stage13_decision = raw_stage13_decision if isinstance(raw_stage13_decision, dict) else {}
    return {
        "global_disable_all_trading_present": disable_path.exists(),
        "stage13_status": stage13_decision.get("status") or raw_stage13_decision,
        "stage13_current_blocker": stage13.get("current_blocked_state")
        or stage13_decision.get("primary_blocker"),
        "tiny_live_firewall_decision": (intent.get("firewall") or {}).get("decision"),
        "tiny_live_broker_submit_attempt_status": intent.get("broker_submit_attempt_status"),
        "real_orders": intent.get("real_orders", intent.get("safety", {}).get("real_orders", 0)),
        "private_submit_used": intent.get("private_submit_used", intent.get("safety", {}).get("private_submit_used", False)),
    }


def build_report() -> dict[str, Any]:
    bithumb = summarize_bithumb()
    kis = summarize_kis()
    safety = summarize_safety()

    completion_audit = {
        "bithumb_axis_inventory_present": bool(bithumb["counts"]["latest_verified_leaderboard_models"]),
        "kis_axis_inventory_present": bool(kis["counts"]["verified_registry_candidates_all_axes"]),
        "leaders_present": bool(bithumb["leaders"]["current_actionable_top_signal"]) and bool(kis["leaders"]["stock_risk_conversion_top"]),
        "evidence_files_recorded": bool(bithumb["evidence_files"]) and bool(kis["evidence_files"]),
        "bithumb_verification_sources_recorded": bool(
            bithumb["verification_sources"].get("oos_top_candidate_id")
            and bithumb["verification_sources"].get("robustness_source_oos")
        ),
        "kis_verification_sources_recorded": bool(
            kis["verification_sources"].get("direct_source_bridge")
            and kis["verification_sources"].get("bridge_universe_validation_mode")
            and kis["verification_sources"].get("bridge_universe_validation_verifier_status")
        ),
        "no_order_submission_performed_by_inventory": safety.get("real_orders") in (0, None),
    }
    completion_audit["status"] = "COMPLETE" if all(completion_audit.values()) else "INCOMPLETE"

    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "report": "two_axis_model_inventory",
        "scope": "file_backed_latest_inventory_not_full_git_history",
        "axes": {
            "BITHUMB_KRW": bithumb,
            "KIS_COMBINED_KRW": kis,
        },
        "safety": safety,
        "completion_audit": completion_audit,
    }


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.tmp")
    temp.write_text(text, encoding="utf-8")
    temp.replace(path)


def write_markdown(report: dict[str, Any]) -> None:
    b = report["axes"]["BITHUMB_KRW"]
    k = report["axes"]["KIS_COMBINED_KRW"]
    safety = report["safety"]

    top_signal = b["leaders"].get("current_actionable_top_signal") or {}
    top_signal_conv = top_signal.get("source_conversion", {})
    top_stock = (k["leaders"].get("stock_risk_conversion_top") or [{}])[0]
    lines = [
        "# Two Axis Model Inventory",
        "",
        f"- Generated UTC: `{report['generated_at_utc']}`",
        f"- Scope: `{report['scope']}`",
        "",
        "## Summary",
        "",
        "| Axis | Model / Candidate Inventory | Current Leader | Key Status |",
        "|---|---:|---|---|",
        (
            "| BITHUMB_KRW | "
            f"{b['counts']['latest_verified_leaderboard_models']} latest leaderboard, "
            f"{b['counts']['long_history_leaderboard_models']} long-history, "
            f"{b['counts']['current_actionable_parameter_sweeps']} ORCA/Bithumb sweeps | "
            f"{top_signal.get('candidate_id', 'n/a')} | "
            f"{b['counts']['current_actionable_oos_pass']} OOS pass, "
            f"{b['counts']['current_nonzero_signal_candidates']} current nonzero |"
        ),
        (
            "| KIS_COMBINED_KRW | "
            f"{k['counts']['verified_registry_candidates_all_axes']} verified registry candidates, "
            f"{k['counts']['stock_risk_conversion_queue']} stock conversion queue, "
            f"{k['counts']['model_factory_experiment_queue']} experiment queue | "
            f"{top_stock.get('id', 'n/a')} | "
            f"{k['counts']['stock_risk_conversion_ready']} ready conversion candidates |"
        ),
        "",
        "## BITHUMB_KRW",
        "",
        f"- Ready markets: `{b['universe']['ready_market_count']}`; selected markets: `{b['universe']['selected_market_count']}`.",
        f"- Latest verified leaderboard models: `{b['counts']['latest_verified_leaderboard_models']}`.",
        f"- Long-history leaderboard models: `{b['counts']['long_history_leaderboard_models']}`; research watchlist: `{b['counts']['long_history_research_watchlist_models']}`.",
        f"- Current actionable parameter sweeps: `{b['counts']['current_actionable_parameter_sweeps']}`; risk conversions: `{b['counts']['current_actionable_risk_conversions']}`; OOS pass: `{b['counts']['current_actionable_oos_pass']}` / `{b['counts']['current_actionable_oos_evaluations']}`.",
        f"- OOS/robustness source: OOS `{b['verification_sources']['oos_top_candidate_id']}` `{b['verification_sources']['oos_top_market']}` generated `{b['verification_sources']['oos_generated_at']}`; robustness `{b['verification_sources']['robustness_candidate_id']}` generated `{b['verification_sources']['robustness_generated_at']}`; current signal matches OOS top `{b['verification_sources']['current_signal_matches_oos_top']}`.",
        f"- Current signal selection policy: `{(b['verification_sources'].get('current_signal_selection_policy') or {}).get('description') or 'n/a'}`.",
        f"- Current signal selection rank: current `{(b['verification_sources'].get('current_signal_selection_summary') or {}).get('selection_rank')}`, OOS top `{(b['verification_sources'].get('oos_top_signal_selection_summary') or {}).get('selection_rank')}`; estimated CAGR `{pct((b['verification_sources'].get('current_signal_selection_summary') or {}).get('estimated_cagr'))}` vs `{pct((b['verification_sources'].get('oos_top_signal_selection_summary') or {}).get('estimated_cagr'))}`.",
        f"- Current signal near miss: `{(b['verification_sources'].get('current_signal_top_near_miss') or {}).get('candidate_id') or '-'}` rank `{(b['verification_sources'].get('current_signal_top_near_miss') or {}).get('near_miss_rank')}`, momentum gap `{metric((b['verification_sources'].get('current_signal_top_near_miss') or {}).get('momentum_gap'))}`, volume gap `{metric((b['verification_sources'].get('current_signal_top_near_miss') or {}).get('volume_gap'))}`, blockers `{', '.join((b['verification_sources'].get('current_signal_top_near_miss') or {}).get('blocking_conditions') or []) or '-'}`.",
        f"- OOS comparison: current signal avg fold CAGR `{pct((b['verification_sources'].get('current_signal_oos_summary') or {}).get('average_fold_cagr'))}`, OOS top avg fold CAGR `{pct((b['verification_sources'].get('oos_top_summary') or {}).get('average_fold_cagr'))}`; current signal trades `{(b['verification_sources'].get('current_signal_oos_summary') or {}).get('total_trade_count')}`, OOS top trades `{(b['verification_sources'].get('oos_top_summary') or {}).get('total_trade_count')}`.",
        f"- Direct crypto signal split: generated `{b['verification_sources'].get('direct_generated_at_utc') or '-'}`; candidates `{b['verification_sources'].get('direct_crypto_candidate_count')}`; OOS `{b['verification_sources'].get('direct_crypto_oos_pass_count')}`; validated `{b['verification_sources'].get('direct_crypto_validated_pass_count')}`; archive triggered `{b['verification_sources'].get('direct_crypto_archive_signal_triggered_count')}`; top live triggered `{b['verification_sources'].get('direct_crypto_top_live_signal_triggered_count')}`; top live verified `{b['verification_sources'].get('direct_crypto_top_live_signal_all_verified')}`.",
        f"- Direct crypto live near miss: `{(b['verification_sources'].get('direct_crypto_top_live_near_miss_candidate') or {}).get('candidate_id') or '-'}` market `{(b['verification_sources'].get('direct_crypto_top_live_near_miss_candidate') or {}).get('market') or '-'}`, rank `{(b['verification_sources'].get('direct_crypto_top_live_near_miss_candidate') or {}).get('live_near_miss_rank')}`, momentum gap `{metric((b['verification_sources'].get('direct_crypto_top_live_near_miss_candidate') or {}).get('momentum_gap'))}`, volume gap `{metric((b['verification_sources'].get('direct_crypto_top_live_near_miss_candidate') or {}).get('volume_gap'))}`, blockers `{', '.join((b['verification_sources'].get('direct_crypto_top_live_near_miss_candidate') or {}).get('blocking_conditions') or []) or '-'}`.",
        f"- Current nonzero candidates: `{b['counts']['current_nonzero_signal_candidates']}`.",
        (
            f"- Current leader: `{top_signal.get('candidate_id', 'n/a')}` "
            f"market `{top_signal.get('market', 'n/a')}`, estimated CAGR `{pct(top_signal_conv.get('estimated_cagr'))}`, "
            f"estimated MDD `{pct(top_signal_conv.get('estimated_mdd'))}`, profit factor `{metric(top_signal_conv.get('source_profit_factor'))}`."
        ),
        "",
        "## KIS_COMBINED_KRW",
        "",
        f"- Stock/ETF loaded symbols in verified registry: `{k['universe']['stock_etf_loaded_symbols']}`; FX mode: `{k['universe']['fx_mode']}`.",
        f"- Verified candidate registry total: `{k['counts']['verified_registry_candidates_all_axes']}`; stock/ETF promotion candidates currently ready: `{k['counts']['stock_risk_conversion_ready']}`.",
        f"- Stock risk conversion queue: `{k['counts']['stock_risk_conversion_queue']}` candidates; blocked: `{k['counts']['stock_risk_conversion_blocked']}`.",
        f"- Model factory queue: `{k['counts']['model_factory_experiment_queue']}` experiments; ready: `{k['counts']['model_factory_ready_experiments']}`; waiting human review: `{k['counts']['model_factory_waiting_for_human_review']}`.",
        f"- Direct/bridge source: direct generated `{k['verification_sources']['direct_generated_at_utc']}`; bridge `{k['verification_sources']['bridge_candidate_id']}` generated `{k['verification_sources']['bridge_generated_at_utc']}`; universe `{k['verification_sources']['bridge_universe_validation_mode']}`; verifier `{k['verification_sources']['bridge_universe_validation_verifier_status']}`; bridge matches direct top parent `{k['verification_sources']['bridge_matches_direct_top_parent']}`; direct top parent `{k['verification_sources']['direct_top_parent_candidate_id']}`.",
        (
            f"- Current KIS conversion leader: `{top_stock.get('id', 'n/a')}` "
            f"before CAGR `{pct(top_stock.get('before_cagr'))}`, before MDD `{pct(top_stock.get('before_mdd'))}`, "
            f"converted CAGR `{pct(top_stock.get('estimated_cagr'))}`, converted MDD `{pct(top_stock.get('estimated_mdd'))}`, overlay `{top_stock.get('overlay', 'n/a')}`."
        ),
        "",
        "## Safety State",
        "",
        f"- Global disable present: `{safety['global_disable_all_trading_present']}`.",
        f"- Tiny-live firewall decision: `{safety.get('tiny_live_firewall_decision')}`; submit attempt: `{safety.get('tiny_live_broker_submit_attempt_status')}`.",
        f"- Real orders: `{safety.get('real_orders')}`; private submit used: `{safety.get('private_submit_used')}`.",
        "",
        "## Completion Audit",
        "",
    ]

    for key, value in report["completion_audit"].items():
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(["", "## Evidence Files", ""])
    for axis in ("BITHUMB_KRW", "KIS_COMBINED_KRW"):
        lines.append(f"### {axis}")
        for evidence in report["axes"][axis]["evidence_files"]:
            lines.append(f"- `{evidence}`")
        lines.append("")

    atomic_write_text(OUT_MD, "\n".join(lines))


def main() -> None:
    report = build_report()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(OUT_JSON, json.dumps(report, indent=2, ensure_ascii=False))
    write_markdown(report)
    print(json.dumps({
        "json": str(OUT_JSON),
        "markdown": str(OUT_MD),
        "completion_status": report["completion_audit"]["status"],
    }, indent=2))


if __name__ == "__main__":
    main()
