from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


ANALYSIS_DIR = Path("analysis_results")
EXIT_COMPRESSION_PATH = ANALYSIS_DIR / "btc_1d_trend_dip_reversal_breakout_exit_compression_batch_20260415T182455Z.json"
EXIT_SYMMETRY_PATH = ANALYSIS_DIR / "btc_1d_trend_dip_reversal_breakout_exit_symmetry_batch_20260415T210607Z.json"
FRICTION_PATH = ANALYSIS_DIR / "btc_1d_trend_dip_reversal_breakout_tsmh_friction_20260415T211214Z.json"
VALIDATION_PATH = ANALYSIS_DIR / "btc_1d_trend_dip_reversal_breakout_symmetry_v4_btcusdt_1d_2200_paper_validation_20260415T211024Z.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _best_by_mdd(rows: list[dict]) -> dict:
    return min(rows, key=lambda row: (float(row["max_drawdown"]), -float(row["cagr"]), -float(row["sharpe"])))


def _scoreboard_candidate() -> dict:
    scoreboard = _load_json(ANALYSIS_DIR / "btc_1d_model_scoreboard_latest.json")
    rows = list(scoreboard.get("top_models", [])) + list(scoreboard.get("top_new_models", []))
    row = next((item for item in rows if str(item.get("variant")) == "trend_dip_reversal_breakout_tighter_stop_mid_hold"), None)
    return {
        "label": "tighter_stop_mid_hold",
        "strategy_name": "trend_dip_reversal_breakout",
        "cagr": float(row.get("cagr") or 0.0) if row else 0.0,
        "max_drawdown": float(row.get("mdd") or 0.0) if row else 0.0,
        "sharpe": float(row.get("sharpe") or 0.0) if row else 0.0,
        "failed_gates": [str(row.get("gate_failure_reason"))] if row and row.get("gate_failure_reason") else ["missing_archived_artifacts"],
    }


def build_report() -> dict:
    if not (EXIT_COMPRESSION_PATH.exists() and EXIT_SYMMETRY_PATH.exists() and FRICTION_PATH.exists() and VALIDATION_PATH.exists()):
        current_candidate = _scoreboard_candidate()
        placeholder = {
            "variant_label": "missing_archived_artifacts",
            "strategy_name": "missing_archived_artifacts",
            "cagr": 0.0,
            "max_drawdown": 0.0,
            "sharpe": 0.0,
            "completed_trades": 0,
        }
        return {
            "generated_at": datetime.now(tz=UTC).isoformat(),
            "current_candidate": current_candidate,
            "best_exit_compression_variant": placeholder,
            "best_exit_symmetry_variant": placeholder,
            "friction_summary": {
                "final_decision": "unavailable",
                "decision_reason": "archived timestamp artifacts are absent",
            },
            "reopen_verdict": {
                "preferred_mutation_family": "disabled_missing_archived_artifacts",
                "preferred_variant_label": "missing_archived_artifacts",
                "keep_current_candidate_as_drawdown_anchor": True,
                "reason": "Archived trend-dip reopen artifacts are absent; using latest scoreboard candidate and keeping the lane disabled.",
            },
            "decision_summary": [
                "Trend-dip reopen queue is disabled until archived artifacts are regenerated.",
                "This prevents optional attack queue reporting from failing the overnight loop.",
            ],
        }

    compression = _load_json(EXIT_COMPRESSION_PATH)
    symmetry = _load_json(EXIT_SYMMETRY_PATH)
    friction = _load_json(FRICTION_PATH)
    validation = _load_json(VALIDATION_PATH)

    compression_best = _best_by_mdd(compression["results"])
    symmetry_best = _best_by_mdd(symmetry["results"])
    current_candidate = {
        "label": "tighter_stop_mid_hold",
        "strategy_name": validation["config"]["strategy_name"],
        "cagr": float(validation["decision_record"]["key_metrics"]["cagr"]),
        "max_drawdown": float(validation["decision_record"]["key_metrics"]["max_drawdown"]),
        "sharpe": float(validation["decision_record"]["key_metrics"]["sharpe"]),
        "failed_gates": list(validation["decision_record"]["failed_gates"]),
    }

    if float(symmetry_best["max_drawdown"]) <= float(compression_best["max_drawdown"]):
        preferred_mutation_family = "exit_symmetry"
        preferred_variant = symmetry_best
    else:
        preferred_mutation_family = "exit_compression"
        preferred_variant = compression_best

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "current_candidate": current_candidate,
        "best_exit_compression_variant": {
            "variant_label": compression_best["variant_label"],
            "strategy_name": compression_best["strategy_name"],
            "cagr": compression_best["cagr"],
            "max_drawdown": compression_best["max_drawdown"],
            "sharpe": compression_best["sharpe"],
            "completed_trades": compression_best["completed_trades"],
        },
        "best_exit_symmetry_variant": {
            "variant_label": symmetry_best["variant_label"],
            "strategy_name": symmetry_best["strategy_name"],
            "cagr": symmetry_best["cagr"],
            "max_drawdown": symmetry_best["max_drawdown"],
            "sharpe": symmetry_best["sharpe"],
            "completed_trades": symmetry_best["completed_trades"],
        },
        "friction_summary": {
            "final_decision": friction["final_decision"],
            "decision_reason": friction["decision_reason"],
        },
        "reopen_verdict": {
            "preferred_mutation_family": preferred_mutation_family,
            "preferred_variant_label": preferred_variant["variant_label"],
            "keep_current_candidate_as_drawdown_anchor": bool(
                float(current_candidate["max_drawdown"]) <= float(preferred_variant["max_drawdown"])
            ),
            "reason": (
                "Exit compression variants did not beat the current tighter-stop mid-hold candidate on drawdown, "
                "and the symmetry family still contains the lowest-drawdown validated shape."
                if preferred_mutation_family == "exit_symmetry"
                else "Exit compression produced the lowest-drawdown reopen path."
            ),
        },
        "decision_summary": [
            (
                "Do not reopen the trend-dip family through exit-compression-first alone because the best compression variant "
                "still sits above the current tighter-stop mid-hold on drawdown."
            ),
            (
                f"Use `{preferred_variant['variant_label']}` from `{preferred_mutation_family}` as the next mutation reference if the family is reopened."
            ),
            f"Keep the current tighter-stop mid-hold candidate as the drawdown anchor until friction and overfitting gates improve from `{friction['final_decision']}`.",
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    current = report["current_candidate"]
    compression = report["best_exit_compression_variant"]
    symmetry = report["best_exit_symmetry_variant"]
    verdict = report["reopen_verdict"]
    friction = report["friction_summary"]
    return "\n".join(
        [
            "# BTC 1d Trend Dip Attack Reopen Screen",
            "",
            f"- Current candidate: `{current['label']}`",
            f"- Current base: `{current['cagr']:.4f}` CAGR / `{current['max_drawdown']:.4f}` MDD / Sharpe `{current['sharpe']:.4f}`",
            f"- Best exit compression: `{compression['variant_label']}` | `{compression['cagr']:.4f}` CAGR / `{compression['max_drawdown']:.4f}` MDD / Sharpe `{compression['sharpe']:.4f}`",
            f"- Best exit symmetry: `{symmetry['variant_label']}` | `{symmetry['cagr']:.4f}` CAGR / `{symmetry['max_drawdown']:.4f}` MDD / Sharpe `{symmetry['sharpe']:.4f}`",
            f"- Friction status: `{friction['final_decision']}`",
            f"- Preferred mutation family: `{verdict['preferred_mutation_family']}`",
            f"- Preferred variant label: `{verdict['preferred_variant_label']}`",
            f"- Keep current candidate as drawdown anchor: `{verdict['keep_current_candidate_as_drawdown_anchor']}`",
            f"- Reason: {verdict['reason']}",
            "",
        ]
    )


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_trend_dip_attack_reopen_screen_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_trend_dip_attack_reopen_screen_{stamp}.md"
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
