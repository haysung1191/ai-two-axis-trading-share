from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


ANALYSIS_DIR = Path("analysis_results")


def _latest_batch_path(analysis_dir: Path) -> Path:
    matches = sorted(
        analysis_dir.glob("btc_1d_failed_breakout_continuation_hold_refinement_batch_*.json"),
        key=lambda path: path.name,
    )
    if not matches:
        raise FileNotFoundError("No failed breakout continuation hold refinement batch artifact found.")
    return matches[-1]


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _best_variant(rows: list[dict]) -> dict:
    def _candidate_ready(row: dict) -> bool:
        return (
            row.get("stage") == "stage2"
            and bool(row.get("stage1_passed", False))
            and len(row.get("overfitting_flags", [])) == 0
            and float(row["max_drawdown"]) <= 0.16
            and float(row["cagr"]) >= 0.20
            and float(row.get("trades", 0)) >= 10
        )

    return min(
        rows,
        key=lambda row: (
            not _candidate_ready(row),
            row.get("stage") != "stage2",
            row.get("decision") != "KEEP",
            not bool(row.get("stage1_passed", False)),
            len(row.get("overfitting_flags", [])) > 0,
            -float(row["cagr"]),
            -float(row.get("trades", 0)),
            float(row["max_drawdown"]),
            -float(row["sharpe"]),
        ),
    )


def build_report_from_batch(batch: dict) -> dict:
    best = _best_variant(batch["results"])
    ready = (
        best.get("stage") == "stage2"
        and bool(best.get("stage1_passed", False))
        and len(best.get("overfitting_flags", [])) == 0
        and float(best["max_drawdown"]) <= 0.16
        and float(best["cagr"]) >= 0.20
        and float(best.get("trades", 0)) >= 10
    )
    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "batch_run_id": batch["run_id"],
        "stage1_survivors": list(batch.get("stage1_survivors", [])),
        "best_variant": {
            "variant_label": best["variant_label"],
            "strategy_name": best["strategy_name"],
            "stage": best["stage"],
            "decision": best["decision"],
            "cagr": float(best["cagr"]),
            "max_drawdown": float(best["max_drawdown"]),
            "sharpe": float(best["sharpe"]),
            "trades": int(best["trades"]),
            "completed_trades": int(best["completed_trades"]),
            "overfitting_flags": list(best.get("overfitting_flags", [])),
            "sensitivity_max_drift": float(best.get("sensitivity_max_drift", 0.0)),
        },
        "hold_refinement_verdict": {
            "promoted_to_candidate_stage": ready,
            "next_step": "candidate_stage_followup" if ready else "hold_revisit_exhausted_or_reframed",
            "reason": (
                "The failed-breakout hold refinement cleared candidate-stage and should move into candidate follow-up."
                if ready
                else "The failed-breakout hold refinement still could not clear candidate-stage, so this hold either needs reframing or should be treated as exhausted."
            ),
        },
        "decision_summary": [
            (
                f"Best hold refinement variant is `{best['variant_label']}` with `{float(best['cagr']):.4f}` CAGR, "
                f"`{float(best['max_drawdown']):.4f}` MDD, and `{int(best['trades'])}` trades."
            ),
            "Advance only if the failed-breakout hold can cross the candidate-stage bar without losing clean stage2 behavior.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare failed breakout continuation hold refinement results.")
    parser.add_argument("--batch-json", type=Path, default=None)
    parser.add_argument("--analysis-dir", type=Path, default=ANALYSIS_DIR)
    args = parser.parse_args(argv)

    batch_path = args.batch_json or _latest_batch_path(args.analysis_dir)
    report = build_report_from_batch(_load_json(batch_path))
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = args.analysis_dir / f"btc_1d_failed_breakout_hold_refinement_screen_{stamp}.json"
    md_path = args.analysis_dir / f"btc_1d_failed_breakout_hold_refinement_screen_{stamp}.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_lines = [
        "# BTC 1d Failed Breakout Hold Refinement Screen",
        "",
        f"- Best variant: `{report['best_variant']['variant_label']}`",
        f"- Stage: `{report['best_variant']['stage']}`",
        f"- Decision: `{report['best_variant']['decision']}`",
        f"- Base: `{report['best_variant']['cagr']:.4f}` CAGR / `{report['best_variant']['max_drawdown']:.4f}` MDD / Sharpe `{report['best_variant']['sharpe']:.4f}`",
        f"- Trades: `{report['best_variant']['trades']}`",
        f"- Promoted to candidate-stage: `{report['hold_refinement_verdict']['promoted_to_candidate_stage']}`",
        f"- Next step: `{report['hold_refinement_verdict']['next_step']}`",
        f"- Reason: {report['hold_refinement_verdict']['reason']}",
        "",
    ]
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(json.dumps({"report_json_path": str(json_path), "report_md_path": str(md_path), "report": report}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
