from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


ANALYSIS_DIR = Path("analysis_results")
CANDIDATE_LABEL = "volatility_spike_reversal_continuation_tighter_stop"
REPAIR_MAX_DRAWDOWN_TARGET = 0.25


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _latest_path(pattern: str) -> Path:
    matches = sorted(
        ANALYSIS_DIR.glob(pattern),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not matches:
        raise FileNotFoundError(f"No analysis artifact matched pattern: {pattern}")
    return matches[0]


def _latest_walk_forward_for_candidate(candidate_label: str) -> tuple[Path | None, dict]:
    for path in sorted(
        ANALYSIS_DIR.glob("btc_1d_walk_forward_diagnostic_*.json"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    ):
        payload = _load_json(path)
        if str(payload.get("config", {}).get("candidate_label", "")) == candidate_label:
            return path, payload
    return None, {}


def _negative_window_ids(walk_forward_payload: dict) -> list[int]:
    windows = walk_forward_payload.get("overfitting", {}).get("walk_forward", []) or []
    negative: list[int] = []
    for index, row in enumerate(windows, start=1):
        window_id = int(row.get("window", index))
        cagr = float(row.get("metrics", {}).get("cagr", 0.0))
        if cagr < 0.0:
            negative.append(window_id)
    return negative


def _variant_by_label(rows: list[dict], label: str) -> dict:
    for row in rows:
        if str(row.get("variant_label", "")) == label:
            return dict(row)
    return {}


def _compact_metrics(metrics: dict) -> dict:
    keys = ("trades", "sharpe", "max_drawdown", "win_rate", "cagr")
    return {key: metrics[key] for key in keys if key in metrics}


def build_report() -> dict:
    batch_path = _latest_path("btc_1d_volatility_spike_reversal_continuation_exit_compression_batch_*.json")
    batch = _load_json(batch_path)
    rows = [dict(row) for row in list(batch.get("results", []) or [])]
    stage1_survivors = list(batch.get("stage1_survivors", []) or [])
    best_by_cagr = max(rows, key=lambda row: float(row.get("cagr", 0.0)), default={})
    current_reference = _variant_by_label(rows, "current_reference")
    tighter_stop = _variant_by_label(rows, "tighter_stop")
    wf_path, wf_payload = _latest_walk_forward_for_candidate(CANDIDATE_LABEL)
    negative_windows = _negative_window_ids(wf_payload)
    wf_base_metrics = _compact_metrics(dict(wf_payload.get("base_metrics", {}) or {}))
    mdd_reduction = (
        float(current_reference["max_drawdown"]) - float(tighter_stop["max_drawdown"])
        if current_reference and tighter_stop
        else 0.0
    )
    tighter_stop_mdd = float(tighter_stop.get("max_drawdown", 0.0)) if tighter_stop else 0.0
    repair_found = bool(
        tighter_stop
        and wf_payload
        and tighter_stop_mdd <= REPAIR_MAX_DRAWDOWN_TARGET
        and not negative_windows
    )
    next_step = (
        "open_attack_main_replacement_review"
        if repair_found
        else "close_spike_reversal_exit_compression_axis_and_open_new_return_family"
        if rows and wf_payload
        else "collect_spike_reversal_exit_compression_evidence"
    )
    reason = (
        "Tighter-stop exit compression cleared drawdown and walk-forward negative-window repair checks."
        if repair_found
        else "Tighter stop reduced drawdown, but remained above the repair target or still had negative walk-forward windows."
        if rows and wf_payload
        else "Exit-compression batch or tighter-stop walk-forward evidence is incomplete."
    )
    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "source_batch_json": str(batch_path),
        "source_walk_forward_json": str(wf_path) if wf_path else None,
        "exit_compression_reference": {
            "stage1_survivor_count": len(stage1_survivors),
            "stage1_survivors": stage1_survivors,
            "completed_variant_count": len(rows),
            "repair_max_drawdown_target": REPAIR_MAX_DRAWDOWN_TARGET,
        },
        "best_exit_compression_by_cagr": best_by_cagr,
        "current_reference": current_reference,
        "tighter_stop": tighter_stop,
        "tighter_stop_walk_forward": {
            "candidate_label": CANDIDATE_LABEL,
            "base_metrics": wf_base_metrics,
            "negative_windows": negative_windows,
            "sensitivity_max_drift": float(
                wf_payload.get("overfitting", {}).get("sensitivity_max_drift", 0.0)
            )
            if wf_payload
            else None,
        },
        "exit_compression_verdict": {
            "mdd_reduction_from_current_reference": round(mdd_reduction, 8),
            "negative_window_clean": not negative_windows if wf_payload else False,
            "exit_compression_repair_found": repair_found,
            "completed_axis_failed": bool(rows and wf_payload) and not repair_found,
            "next_step_now": next_step,
            "reason": reason,
        },
        "completed_variants": rows,
        "decision_summary": [
            f"Stage1 survivors: `{len(stage1_survivors)}`.",
            (
                f"Best exit-compression by CAGR is `{best_by_cagr['variant_label']}` with CAGR "
                f"`{float(best_by_cagr['cagr']):.6f}` and MDD `{float(best_by_cagr['max_drawdown']):.6f}`."
                if best_by_cagr
                else "No exit-compression variant is available."
            ),
            (
                f"Tighter stop reduced MDD by `{mdd_reduction:.6f}` to `{tighter_stop_mdd:.6f}`, "
                f"but walk-forward negative windows are `{negative_windows}`."
                if tighter_stop and wf_payload
                else "Tighter-stop walk-forward evidence is incomplete."
            ),
            reason,
        ],
    }


def _render_markdown(report: dict) -> str:
    reference = report["exit_compression_reference"]
    verdict = report["exit_compression_verdict"]
    tighter = report["tighter_stop"]
    wf = report["tighter_stop_walk_forward"]
    lines = [
        "# BTC 1d Volatility Spike Reversal Exit-Compression Review",
        "",
        f"- Stage1 survivors: `{reference['stage1_survivor_count']}`",
        f"- Completed variants: `{reference['completed_variant_count']}`",
        f"- Repair found: `{verdict['exit_compression_repair_found']}`",
        f"- Completed axis failed: `{verdict['completed_axis_failed']}`",
        f"- Next step now: `{verdict['next_step_now']}`",
        f"- Reason: {verdict['reason']}",
        "",
        "## Tighter Stop",
        (
            f"- CAGR: `{float(tighter.get('cagr', 0.0)):.6f}` | MDD: "
            f"`{float(tighter.get('max_drawdown', 0.0)):.6f}` | Sharpe: "
            f"`{float(tighter.get('sharpe', 0.0)):.6f}`"
            if tighter
            else "- No tighter-stop variant found."
        ),
        f"- Walk-forward negative windows: `{wf['negative_windows']}`",
        f"- Sensitivity max drift: `{wf['sensitivity_max_drift']}`",
        "",
        "## Completed Variants",
    ]
    for row in report["completed_variants"]:
        lines.append(
            f"- `{row['variant_label']}` | decision=`{row['decision']}` "
            f"| CAGR=`{float(row['cagr']):.6f}` "
            f"| MDD=`{float(row['max_drawdown']):.6f}` "
            f"| Sharpe=`{float(row['sharpe']):.6f}` "
            f"| failed_gates=`{row.get('failed_gates', [])}`"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_volatility_spike_reversal_exit_compression_review_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_volatility_spike_reversal_exit_compression_review_{stamp}.md"
    latest_json = ANALYSIS_DIR / "btc_1d_volatility_spike_reversal_exit_compression_review_latest.json"
    latest_md = ANALYSIS_DIR / "btc_1d_volatility_spike_reversal_exit_compression_review_latest.md"
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
