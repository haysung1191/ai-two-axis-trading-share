from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pandas as pd


ROOT = REPO_ROOT
SHADOW_DIR = ROOT / "output" / "split_models_shadow"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def _format_money(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{float(value):,.0f}"


def main() -> None:
    summary = _load_json(SHADOW_DIR / "shadow_summary.json")
    readiness = _load_json(SHADOW_DIR / "shadow_live_readiness.json")
    transition = _load_json(SHADOW_DIR / "shadow_live_transition_summary.json")
    execution = _load_json(SHADOW_DIR / "shadow_rebalance_execution_summary.json")
    market_summary = _load_csv(SHADOW_DIR / "shadow_rebalance_market_summary.csv")
    order_sheet = _load_csv(SHADOW_DIR / "shadow_rebalance_orders.csv")

    packet_path = SHADOW_DIR / "shadow_live_transition_packet.md"

    lines: list[str] = []
    lines.append("# Split Models Live Transition Packet")
    lines.append("")
    lines.append(f"- baseline variant: `{summary.get('baseline_variant')}`")
    lines.append(f"- live readiness verdict: `{readiness.get('live_readiness_verdict')}`")
    lines.append(f"- signal date: `{transition.get('signal_date')}`")
    lines.append(f"- current holdings: `{summary.get('current_holdings')}`")
    lines.append(f"- current dominant sector: `{summary.get('current_dominant_sector')}`")
    lines.append(f"- transition weight turnover: `{float(transition.get('weight_turnover', 0.0)):.2%}`")
    runtime_status_path = SHADOW_DIR / "shadow_operator_runtime_status.json"
    if runtime_status_path.exists():
        runtime_status = _load_json(runtime_status_path)
        lines.append(f"- operator gate verdict: `{runtime_status.get('operator_gate_verdict')}`")
        lines.append(f"- archive consistency verdict: `{runtime_status.get('archive_consistency_verdict')}`")
        lines.append(f"- archive stability verdict: `{runtime_status.get('archive_stability_verdict')}`")
        lines.append(f"- archive timeline verdict: `{runtime_status.get('archive_timeline_verdict')}`")
        if runtime_status.get("archive_stability_window") is not None:
            lines.append(
                f"- archive stability window: `{runtime_status.get('archive_stability_window')}` runs"
            )
        if runtime_status.get("archive_timeline_window") is not None:
            lines.append(
                f"- archive timeline window: `{runtime_status.get('archive_timeline_window')}` runs"
            )
        failures = runtime_status.get("operator_gate_failures", [])
        if failures:
            lines.append(f"- operator gate failures: `{'; '.join(str(item) for item in failures)}`")
    lines.append("")
    lines.append("## Readiness checks")
    for check in readiness.get("checks", []):
        status = "PASS" if check.get("Passed") else "FAIL"
        lines.append(
            f"- {check.get('Check')}: `{status}` "
            f"(value={check.get('Value')}, threshold={check.get('Threshold')})"
        )
    lines.append("")
    lines.append("## Market execution summary")
    for _, row in market_summary.iterrows():
        money = _format_money(row["GrossDeltaNotional"]) if "GrossDeltaNotional" in row else "N/A"
        lines.append(
            f"- {row['Market']} {row['ExecutionSide']}: "
            f"`{int(row['OrderCount'])}` orders, "
            f"`{float(row['GrossDeltaWeightPct']):.2f}%` gross weight, "
            f"`{money}` gross notional"
        )
    lines.append("")
    lines.append("## Actionable orders")
    actionable = order_sheet[order_sheet["ExecutionSide"] != "HOLD"].copy()
    for _, row in actionable.iterrows():
        lines.append(
            f"- {row['ExecutionSide']} `{row['Symbol']}` "
            f"({row['Market']} / {row['Sector']}): "
            f"`{float(row['DeltaWeightPct']):.2f}%`"
        )
    lines.append("")
    lines.append("## Operator note")
    lines.append(
        "- If live capital is still on `rule_breadth_it_risk_off`, "
        "this packet is the single-file handoff for transition into `rule_breadth_it_us5_cap`."
    )

    packet_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"packet_path={packet_path}")
    print(f"actionable_rows={len(actionable)}")


if __name__ == "__main__":
    main()
