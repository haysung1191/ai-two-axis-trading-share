from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
INPUT_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_start_shift_repair_sweep"
    / "start_shift_repair_sweep_summary.json"
)
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_start_shift_failure_diagnostic"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _pct(value: float) -> str:
    return f"{value:.2%}"


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion Start-Shift Failure Diagnostic",
        "",
        f"Generated: `{summary['generated_at']}`",
        "",
        "## Status",
        "",
        f"- Decision: `{summary['diagnostic_decision']}`",
        f"- Best failed variant: `{summary['best_variant']}`",
        f"- Best failed params: `{json.dumps(summary['best_params'], sort_keys=True)}`",
        "",
        "## Failed Shift Rows",
        "",
        "| Shift | CAGR | MDD | Sharpe | Neg WF | Defense Count | Last Defense |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in summary["failed_shift_rows"]:
        lines.append(
            f"| {int(row['StartShiftMonths'])} | {_pct(float(row['CAGR']))} | {_pct(float(row['MDD']))} | "
            f"{float(row['Sharpe']):.4f} | {int(row['NegativeCAGRWindows'])} | "
            f"{int(row['DefenseCount'])} | `{row['LastDefenseDate']}` |"
        )
    lines.extend(
        [
            "",
            "## Read",
            "",
            f"- {summary['failure_read']}",
            "",
            "## Next Candidate Direction",
            "",
            f"- {summary['next_candidate_direction']}",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sweep = _load_json(INPUT_JSON)
    best = (sweep.get("ranked_specs") or [])[0]
    failed_shift_rows = [
        row
        for row in best.get("shift_rows", [])
        if int(row.get("NegativeCAGRWindows", 0)) > 0 or not bool(row.get("PassMetrics"))
    ]
    failed_shift_ids = [int(row.get("StartShiftMonths")) for row in failed_shift_rows]
    last_defense_dates = sorted({str(row.get("LastDefenseDate")) for row in failed_shift_rows if row.get("LastDefenseDate")})
    defense_counts = sorted({int(row.get("DefenseCount", 0)) for row in failed_shift_rows})
    summary = {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "diagnostic_decision": "START_SHIFT_FAILURE_PATTERN_IDENTIFIED",
        "source": str(INPUT_JSON),
        "best_variant": best.get("variant"),
        "best_params": sweep.get("best_params"),
        "failed_shift_ids": failed_shift_ids,
        "failed_shift_rows": failed_shift_rows,
        "failed_last_defense_dates": last_defense_dates,
        "failed_defense_counts": defense_counts,
        "failure_read": (
            "The best available state-condition defense still fails when the signal calendar is shifted by "
            f"{failed_shift_ids}. The failure is not broad performance collapse: CAGR and MDD remain strong, "
            "but one walk-forward CAGR comparison turns negative after the defense schedule shifts."
        ),
        "next_candidate_direction": (
            "Search for a candidate that keeps the strong MDD compression but does not depend on an early fixed "
            "defense-count budget. Prefer an observable rolling-risk trigger or a candidate-family replacement "
            "over further max_defense_count micro-tuning."
        ),
        "safety": {
            "paper_enabled": False,
            "live_enabled": False,
            "broker_submit_allowed": False,
            "order_intent_created": False,
        },
    }
    (OUTPUT_DIR / "start_shift_failure_diagnostic_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "start_shift_failure_diagnostic.md").write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
