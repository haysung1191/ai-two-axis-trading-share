from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check whether the BTC 1d hold36 local pressure-watch ceiling remains intact. "
            "Returns non-zero when the confirmed local ceiling contract has drifted."
        )
    )
    parser.add_argument("--analysis-dir", type=Path, default=Path("analysis_results"))
    parser.add_argument("--as-json", action="store_true")
    return parser


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check_hold36_local_ceiling(*, analysis_dir: Path) -> dict[str, Any]:
    handoff = _load_json(analysis_dir / "btc_1d_hold36_local_ceiling_handoff_latest.json")
    reference = handoff["handoff_reference"]
    status = handoff["local_ceiling_status"]
    metrics = handoff["handoff_metrics"]

    expected_backup = "post_spike_trend92_depth058_volume105_hold36"
    required_closed_axes = {
        "challenger_reopen",
        "base_gap_recovery",
        "entry_timing",
        "entry_strength",
        "structure",
    }
    closed_axes = set(status.get("closed_local_axes", []))

    checks = {
        "backup_label_ok": str(reference.get("active_backup")) == expected_backup,
        "status_band_ok": str(status.get("status_band")) == "pressure_watch",
        "ceiling_confirmed_ok": bool(status.get("ceiling_confirmed")) is True,
        "base_blocker_ok": str(status.get("primary_blocker")) == "base_cagr_gap",
        "cost_gap_closed_ok": float(status.get("remaining_cost20_cagr_gap_to_open", 1.0)) == 0.0,
        "do_not_repeat_ok": bool(status.get("do_not_repeat_local_loop")) is True,
        "closed_axes_complete_ok": required_closed_axes.issubset(closed_axes),
        "base_gap_still_open_ok": float(status.get("remaining_base_cagr_gap_to_open", 0.0)) > 0.0,
        "quality_edge_ok": (
            float(metrics.get("sharpe_edge_vs_main", 0.0)) > 0.15
            and float(metrics.get("mdd_improvement_vs_main", 0.0)) > 0.05
            and float(metrics.get("drift_improvement_vs_main", 0.0)) > 0.15
        ),
    }

    ok = all(checks.values())
    failed_checks = [name for name, passed in checks.items() if not passed]

    return {
        "ok": ok,
        "expected_backup": expected_backup,
        "active_backup": reference.get("active_backup"),
        "status_band": status.get("status_band"),
        "primary_blocker": status.get("primary_blocker"),
        "remaining_base_cagr_gap_to_open": status.get("remaining_base_cagr_gap_to_open"),
        "remaining_cost20_cagr_gap_to_open": status.get("remaining_cost20_cagr_gap_to_open"),
        "closed_local_axes": sorted(closed_axes),
        "failed_checks": failed_checks,
        "checks": checks,
    }


def render_hold36_local_ceiling_line(result: dict[str, Any]) -> str:
    ok = "True" if result["ok"] else "False"
    return (
        f"BTC 1d hold36 local ceiling | ok={ok} | backup={result['active_backup']} | "
        f"status={result['status_band']} | blocker={result['primary_blocker']} | "
        f"base_gap={result['remaining_base_cagr_gap_to_open']} | "
        f"cost_gap={result['remaining_cost20_cagr_gap_to_open']} | "
        f"failed_checks={len(result['failed_checks'])}"
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = check_hold36_local_ceiling(analysis_dir=args.analysis_dir)
    if args.as_json:
        print(json.dumps(result, indent=2))
    else:
        print(render_hold36_local_ceiling_line(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
