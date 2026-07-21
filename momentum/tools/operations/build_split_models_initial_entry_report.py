from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pandas as pd


ROOT = REPO_ROOT
SHADOW_DIR = ROOT / "output" / "split_models_shadow"


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _format_krw(value: float | int | None) -> str:
    if value is None:
        return "-"
    return f"{float(value):,.0f} KRW"


def build_report_text(
    capital_readiness: dict[str, object],
    preflight: dict[str, object],
    plan: pd.DataFrame,
    *,
    capital_slug: str,
    submit_summary: dict[str, object] | None = None,
    submit_results: pd.DataFrame | None = None,
) -> str:
    planned = plan[plan["Status"] == "PLANNED"].copy()
    lines: list[str] = []
    lines.append("# Split Models Initial Entry Report")
    lines.append("")
    lines.append(f"- Capital: `{capital_slug}`")
    lines.append(f"- Preflight verdict: `{preflight.get('preflight_verdict', '-')}`")
    lines.append(f"- Live readiness: `{preflight.get('live_readiness', '-')}`")
    lines.append(f"- Operator gate: `{preflight.get('operator_gate_verdict', '-')}`")
    lines.append(f"- Submit mode checked: `{preflight.get('submit_mode', '-')}`")
    lines.append("")
    lines.append("## Capital Readiness")
    lines.append("")
    lines.append(f"- Fundable names at capital: `{capital_readiness.get('fundable_count_at_capital', 0)}`")
    lines.append(f"- Fundable symbols at capital: `{', '.join(capital_readiness.get('fundable_symbols_at_capital', [])) or '-'}`")
    lines.append(
        f"- Minimum capital for one share across all current holdings: `{_format_krw(capital_readiness.get('min_capital_all_holdings_one_share_krw'))}`"
    )
    lines.append(
        f"- Max single-name one-share cost: `{_format_krw(capital_readiness.get('max_single_name_one_share_cost_krw'))}`"
    )
    lines.append("")
    lines.append("## Planned Orders")
    lines.append("")
    lines.append(f"- Planned count: `{preflight.get('planned_count', 0)}`")
    lines.append(f"- Skipped count: `{preflight.get('skipped_count', 0)}`")
    lines.append(f"- Planned symbols: `{', '.join(preflight.get('planned_symbols', [])) or '-'}`")
    lines.append(f"- Planned quantity total: `{preflight.get('planned_quantity_total', 0)}`")
    lines.append(
        f"- Estimated order notional total: `{_format_krw(preflight.get('estimated_order_notional_krw_total'))}`"
    )
    lines.append("")
    lines.append("| Symbol | Side | Qty | Est. KRW | Exchange |")
    lines.append("| --- | --- | ---: | ---: | --- |")
    for _, row in planned.iterrows():
        lines.append(
            f"| {row['Symbol']} | {row['ExecutionSide']} | {int(row['Quantity'])} | {float(row['EstimatedOrderNotionalKRW']):,.0f} | {row['ResolvedExchange']} |"
        )
    if planned.empty:
        lines.append("| - | - | 0 | 0 | - |")
    lines.append("")
    lines.append("## Integrity")
    lines.append("")
    lines.append(f"- Plan path: `{preflight.get('execution_plan_path', '-')}`")
    lines.append(f"- Plan sha256: `{preflight.get('execution_plan_sha256', '-')}`")
    lines.append(f"- Summary path: `{preflight.get('execution_summary_path', '-')}`")
    lines.append(f"- Summary sha256: `{preflight.get('execution_summary_sha256', '-')}`")
    lines.append("")
    if submit_summary is not None:
        lines.append("## Submission")
        lines.append("")
        lines.append(f"- Submit mode: `{submit_summary.get('submit_mode', '-')}`")
        lines.append(f"- Submitted count: `{submit_summary.get('submitted_count', 0)}`")
        lines.append(f"- Failed count: `{submit_summary.get('failed_count', 0)}`")
        lines.append(f"- Submitted plan path: `{submit_summary.get('submitted_plan_path', '-')}`")
        lines.append(f"- Submitted plan sha256: `{submit_summary.get('submitted_plan_sha256', '-')}`")
        lines.append(f"- Preflight path used at submit: `{submit_summary.get('preflight_path', '-')}`")
        lines.append(f"- Preflight sha256 used at submit: `{submit_summary.get('preflight_sha256', '-')}`")
        lines.append(f"- Check timestamp used at submit: `{submit_summary.get('check_timestamp', '-')}`")
        lines.append(f"- Check latest JSON path: `{submit_summary.get('check_json_path', '-')}`")
        lines.append(f"- Check latest Markdown path: `{submit_summary.get('check_md_path', '-')}`")
        lines.append(f"- Check history JSON path: `{submit_summary.get('check_history_json_path', '-')}`")
        lines.append(f"- Check history Markdown path: `{submit_summary.get('check_history_md_path', '-')}`")
        lines.append("")
        if submit_results is not None and not submit_results.empty:
            lines.append("| Symbol | Side | Qty | Submit Status | Order No | Reason |")
            lines.append("| --- | --- | ---: | --- | --- | --- |")
            for _, row in submit_results.iterrows():
                reason = row.get("SubmitReason", "") or ""
                order_no = row.get("OrderNo", "") or ""
                qty = int(row["Quantity"]) if pd.notna(row.get("Quantity")) else 0
                lines.append(
                    f"| {row.get('Symbol', '-')} | {row.get('ExecutionSide', '-')} | {qty} | {row.get('SubmitStatus', '-')} | {order_no} | {reason} |"
                )
            lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append(
        f"- Archive stability verdict is `{preflight.get('archive_stability_verdict', '-')}` and is reported for context, but current submit gate is driven by live readiness and operator gate."
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capital-readiness-summary-path", required=True)
    parser.add_argument("--preflight-path", required=True)
    parser.add_argument("--plan-path", required=True)
    parser.add_argument("--out-path", required=True)
    parser.add_argument("--capital-slug", default="")
    parser.add_argument("--submit-summary-path", default="")
    parser.add_argument("--submit-results-path", default="")
    args = parser.parse_args(argv)

    capital_readiness = _load_json(Path(args.capital_readiness_summary_path))
    preflight = _load_json(Path(args.preflight_path))
    plan = pd.read_csv(Path(args.plan_path))
    submit_summary = _load_json(Path(args.submit_summary_path)) if args.submit_summary_path else None
    submit_results = pd.read_csv(Path(args.submit_results_path)) if args.submit_results_path else None
    capital_slug = args.capital_slug or str(capital_readiness.get("evaluated_total_capital", "unknown"))
    text = build_report_text(
        capital_readiness,
        preflight,
        plan,
        capital_slug=capital_slug,
        submit_summary=submit_summary,
        submit_results=submit_results,
    )

    out_path = Path(args.out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")

    print(f"report_path={out_path}")


if __name__ == "__main__":
    main()
