from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ANALYSIS_DIR = Path("analysis_results")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _pick_current_hold36_baseline(rows: list[dict]) -> dict | None:
    preferred_labels = (
        "trend864_depth055_volume100_hold36",
        "active_baseline",
        "trend960_depth055_volume100_hold36",
    )
    for label in preferred_labels:
        match = next((row for row in rows if str(row.get("variant_label")) == label), None)
        if match is not None:
            return match
    hold36_rows = [row for row in rows if "hold36" in str(row.get("variant_label", ""))]
    return hold36_rows[0] if hold36_rows else None


def build_report(analysis_dir: Path = ANALYSIS_DIR) -> dict:
    active_source = _load_json(analysis_dir / "btc_1d_attack_challenger_rotation_review_latest.json")
    sensitivity_source = _load_json(
        analysis_dir / "btc_1d_post_spike_consolidation_breakout_sensitivity_repair_batch_latest.json"
    )
    walk_forward_source = _load_json(
        analysis_dir / "btc_1d_post_spike_consolidation_breakout_walk_forward_repair_batch_latest.json"
    )

    active_reference = dict(active_source["active_challenger_reference"])
    walk_forward_rows = list(walk_forward_source.get("results", []))
    current_hold36 = _pick_current_hold36_baseline(walk_forward_rows)

    candidates = []
    for row in sensitivity_source.get("results", []):
        label = str(row.get("variant_label", ""))
        if "hold36" not in label:
            continue
        candidate = {
            "variant_label": label,
            "decision": str(row.get("decision")),
            "base_cagr": float(row["cagr"]),
            "base_sharpe": float(row["sharpe"]),
            "base_max_drawdown": float(row["max_drawdown"]),
            "sensitivity_max_drift": float(row["sensitivity_max_drift"]),
            "failed_gates": list(row.get("failed_gates", [])),
            "overfitting_flags": list(row.get("overfitting_flags", [])),
            "parameters": dict(row.get("parameters", {})),
            "cagr_delta_vs_active": float(row["cagr"]) - float(active_reference["paper_validation_cagr"]),
            "sharpe_delta_vs_active": float(row["sharpe"]) - float(active_reference["paper_validation_sharpe"]),
            "max_drawdown_delta_vs_active": (
                float(active_reference["paper_validation_max_drawdown"]) - float(row["max_drawdown"])
            ),
            "drift_delta_vs_active": (
                float(active_reference["sensitivity_max_drift"]) - float(row["sensitivity_max_drift"])
            ),
            "cagr_delta_vs_current_hold36": (
                float(row["cagr"]) - float(current_hold36["base_cagr"])
                if current_hold36 is not None
                else None
            ),
            "drift_delta_vs_current_hold36": (
                float(current_hold36["sensitivity_max_drift"]) - float(row["sensitivity_max_drift"])
                if current_hold36 is not None
                else None
            ),
            "beats_active_rotation_gate": (
                float(row["cagr"]) > float(active_reference["paper_validation_cagr"])
                and float(row["sharpe"]) > float(active_reference["paper_validation_sharpe"])
                and float(row["max_drawdown"]) <= float(active_reference["paper_validation_max_drawdown"])
                and float(row["sensitivity_max_drift"]) <= float(active_reference["sensitivity_max_drift"])
                and not row.get("failed_gates")
                and not row.get("overfitting_flags")
            ),
        }
        candidates.append(candidate)

    candidates.sort(
        key=lambda item: (
            not item["beats_active_rotation_gate"],
            item["sensitivity_max_drift"],
            -item["base_cagr"],
            -item["base_sharpe"],
        )
    )
    top_candidate = candidates[0] if candidates else None

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "source_artifacts": {
            "attack_challenger_rotation_review": str(
                analysis_dir / "btc_1d_attack_challenger_rotation_review_latest.json"
            ),
            "sensitivity_repair_batch": str(
                analysis_dir / "btc_1d_post_spike_consolidation_breakout_sensitivity_repair_batch_latest.json"
            ),
            "walk_forward_repair_batch": str(
                analysis_dir / "btc_1d_post_spike_consolidation_breakout_walk_forward_repair_batch_latest.json"
            ),
        },
        "active_challenger_reference": active_reference,
        "current_hold36_baseline": (
            {
                "variant_label": str(current_hold36["variant_label"]),
                "base_cagr": float(current_hold36["base_cagr"]),
                "base_sharpe": float(current_hold36["base_sharpe"]),
                "base_max_drawdown": float(current_hold36["base_max_drawdown"]),
                "sensitivity_max_drift": float(current_hold36["sensitivity_max_drift"]),
            }
            if current_hold36 is not None
            else None
        ),
        "hold36_drift_repair_candidates": candidates,
        "drift_repair_verdict": {
            "candidate_found": top_candidate is not None,
            "top_candidate": top_candidate["variant_label"] if top_candidate is not None else None,
            "top_candidate_beats_active_rotation_gate": (
                bool(top_candidate["beats_active_rotation_gate"]) if top_candidate is not None else False
            ),
            "next_step_now": (
                "validate_hold36_drift_repair_candidate_against_active_challenger"
                if top_candidate is not None and top_candidate["beats_active_rotation_gate"]
                else "continue_hold36_drift_repair_search"
            ),
            "reason": (
                f"{top_candidate['variant_label']} clears the active challenger rotation gate while improving drift by "
                f"{top_candidate['drift_delta_vs_active']:.4f} versus {active_reference['label']}."
                if top_candidate is not None and top_candidate["beats_active_rotation_gate"]
                else "No scanned hold36-family sensitivity repair candidate clears the active challenger rotation gate yet."
            ),
        },
        "decision_summary": [
            (
                f"Use `{active_reference['label']}` as the active challenger reference and `{current_hold36['variant_label']}` as the current drift-gap baseline."
                if current_hold36 is not None
                else f"Use `{active_reference['label']}` as the active challenger reference while the drift-gap baseline remains unset."
            ),
            (
                f"`{top_candidate['variant_label']}` is the strongest hold36-family drift repair candidate."
                if top_candidate is not None
                else "No hold36-family drift repair candidate was found."
            ),
            (
                f"Next attack research step: `validate_hold36_drift_repair_candidate_against_active_challenger`."
                if top_candidate is not None and top_candidate["beats_active_rotation_gate"]
                else "Next attack research step: `continue_hold36_drift_repair_search`."
            ),
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    verdict = report["drift_repair_verdict"]
    active = report["active_challenger_reference"]
    baseline = report["current_hold36_baseline"]
    lines = [
        "# BTC 1d Post-Spike Hold36 Drift Repair Candidates",
        "",
        f"- Active challenger: `{active['label']}`",
        f"- Active drift: `{active['sensitivity_max_drift']}`",
        f"- Current hold36 baseline: `{baseline['variant_label']}`" if baseline is not None else "- Current hold36 baseline: `n/a`",
        f"- Current hold36 drift: `{baseline['sensitivity_max_drift']}`" if baseline is not None else "- Current hold36 drift: `n/a`",
        f"- Top candidate: `{verdict['top_candidate']}`",
        f"- Top candidate beats active rotation gate: `{verdict['top_candidate_beats_active_rotation_gate']}`",
        f"- Next step now: `{verdict['next_step_now']}`",
        f"- Reason: {verdict['reason']}",
        "",
        "## Candidates",
    ]
    for row in report["hold36_drift_repair_candidates"]:
        lines.extend(
            [
                f"- `{row['variant_label']}` | decision=`{row['decision']}` | gate=`{row['beats_active_rotation_gate']}`",
                f"  CAGR=`{row['base_cagr']}` Sharpe=`{row['base_sharpe']}` MDD=`{row['base_max_drawdown']}` drift=`{row['sensitivity_max_drift']}`",
                f"  delta_vs_active: cagr=`{row['cagr_delta_vs_active']}` sharpe=`{row['sharpe_delta_vs_active']}` mdd=`{row['max_drawdown_delta_vs_active']}` drift=`{row['drift_delta_vs_active']}`",
                f"  delta_vs_current_hold36: cagr=`{row['cagr_delta_vs_current_hold36']}` drift=`{row['drift_delta_vs_current_hold36']}`",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_post_spike_hold36_drift_repair_candidates_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_post_spike_hold36_drift_repair_candidates_{stamp}.md"
    latest_json = ANALYSIS_DIR / "btc_1d_post_spike_hold36_drift_repair_candidates_latest.json"
    latest_md = ANALYSIS_DIR / "btc_1d_post_spike_hold36_drift_repair_candidates_md_latest.md"
    json_payload = json.dumps(report, indent=2)
    md_payload = _render_markdown(report)
    json_path.write_text(json_payload, encoding="utf-8")
    md_path.write_text(md_payload, encoding="utf-8")
    latest_json.write_text(json_payload, encoding="utf-8")
    latest_md.write_text(md_payload, encoding="utf-8")
    print(
        json.dumps(
            {
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "latest_json_path": str(latest_json),
                "latest_md_path": str(latest_md),
                "report": report,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
