from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


ANALYSIS_DIR = Path("analysis_results")


def _latest_batch_path(analysis_dir: Path) -> Path:
    matches = sorted(
        analysis_dir.glob("btc_1d_shallow_liquidity_void_refill_micro_refinement_batch_*.json"),
        key=lambda path: path.name,
    )
    if not matches:
        raise FileNotFoundError("No shallow liquidity void refill micro refinement batch artifact found.")
    return matches[-1]


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _best_variant(rows: list[dict]) -> dict:
    return min(
        rows,
        key=lambda row: (
            row.get("stage") != "stage2",
            not bool(row.get("stage1_passed", False)),
            len(row.get("overfitting_flags", [])),
            float(row.get("sensitivity_max_drift", 0.0)),
            float(row["max_drawdown"]),
            -float(row["cagr"]),
            -float(row["sharpe"]),
        ),
    )


def build_report_from_batch(batch: dict) -> dict:
    best = _best_variant(batch["results"])
    ready = (
        best.get("stage") == "stage2"
        and bool(best.get("stage1_passed", False))
        and len(best.get("overfitting_flags", [])) == 0
        and float(best.get("sensitivity_max_drift", 1.0)) <= 0.18
        and float(best["max_drawdown"]) <= 0.18
        and float(best["cagr"]) >= 0.22
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
            "overfitting_flags": list(best.get("overfitting_flags", [])),
            "sensitivity_max_drift": float(best.get("sensitivity_max_drift", 0.0)),
            "unstable_parameters": list(best.get("unstable_parameters", [])),
        },
        "micro_refinement_verdict": {
            "has_friction_ready_seed": ready,
            "next_step": "friction_retest" if ready else "lane_exhausted_or_new_family_search",
            "reason": (
                "A micro-refinement mutation compressed sensitivity enough to move the lane into friction retest."
                if ready
                else "Even the best micro-refinement mutation cannot compress sensitivity enough, so this lane is approaching exhaustion and should be compared against opening a new family search."
            ),
        },
        "decision_summary": [
            (
                f"Best micro-refinement mutation is `{best['variant_label']}` with "
                f"{len(best.get('overfitting_flags', []))} overfitting flags and drift `{float(best.get('sensitivity_max_drift', 0.0)):.4f}`."
            ),
            "If this micro-refinement still cannot get drift to 0.18 or below, the lane should be treated as close to exhausted rather than kept in an open-ended repair loop.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare shallow liquidity void refill micro refinement batch results.")
    parser.add_argument("--batch-json", type=Path, default=None)
    parser.add_argument("--analysis-dir", type=Path, default=ANALYSIS_DIR)
    args = parser.parse_args(argv)

    batch_path = args.batch_json or _latest_batch_path(args.analysis_dir)
    report = build_report_from_batch(_load_json(batch_path))
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = args.analysis_dir / f"btc_1d_shallow_liquidity_void_refill_micro_refinement_screen_{stamp}.json"
    md_path = args.analysis_dir / f"btc_1d_shallow_liquidity_void_refill_micro_refinement_screen_{stamp}.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_lines = [
        "# BTC 1d Shallow Liquidity Void Refill Micro Refinement Screen",
        "",
        f"- Best variant: `{report['best_variant']['variant_label']}`",
        f"- Stage: `{report['best_variant']['stage']}`",
        f"- Decision: `{report['best_variant']['decision']}`",
        f"- Base: `{report['best_variant']['cagr']:.4f}` CAGR / `{report['best_variant']['max_drawdown']:.4f}` MDD / Sharpe `{report['best_variant']['sharpe']:.4f}`",
        f"- Overfitting flags: `{', '.join(report['best_variant']['overfitting_flags']) or '-'}`",
        f"- Sensitivity drift: `{report['best_variant']['sensitivity_max_drift']:.4f}`",
        f"- Has friction-ready seed: `{report['micro_refinement_verdict']['has_friction_ready_seed']}`",
        f"- Next step: `{report['micro_refinement_verdict']['next_step']}`",
        f"- Reason: {report['micro_refinement_verdict']['reason']}",
        "",
    ]
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(json.dumps({"report_json_path": str(json_path), "report_md_path": str(md_path), "report": report}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
