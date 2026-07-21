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


def _window_summary(diagnostic: dict, *, target_window: int = 2) -> dict:
    walk_forward = list(((diagnostic.get("overfitting") or {}).get("walk_forward") or []))
    row = next(item for item in walk_forward if int(item.get("window", 0)) == target_window)
    metrics = dict(row.get("metrics") or {})
    timestamps = list(metrics.get("equity_timestamps") or [])
    trade_ledger = list(metrics.get("trade_ledger") or [])
    return {
        "window": target_window,
        "trades": int(metrics.get("trades", 0)),
        "sharpe": float(metrics.get("sharpe", 0.0)),
        "cagr": float(metrics.get("cagr", 0.0)),
        "max_drawdown": float(metrics.get("max_drawdown", 0.0)),
        "equity_start": float(((metrics.get("equity_curve_summary") or {}).get("start", 0.0))),
        "equity_end": float(((metrics.get("equity_curve_summary") or {}).get("end", 0.0))),
        "timestamp_start": timestamps[0] if timestamps else None,
        "timestamp_end": timestamps[-1] if timestamps else None,
        "bars": len(timestamps),
        "trade_ledger_count": len(trade_ledger),
        "sample_trade": trade_ledger[0] if trade_ledger else None,
    }


def _load_variant_from_batch(batch_path: Path, variant_label: str) -> dict:
    batch = _load_json(batch_path)
    rows = list(batch.get("results") or [])
    return next(row for row in rows if str(row.get("variant_label")) == variant_label)


def build_report(analysis_dir: Path = ANALYSIS_DIR) -> dict:
    stage3_batch = _load_json(analysis_dir / "btc_1d_post_spike_idle_window_followup_stage3_batch_latest.json")
    entry_shape_batch = _load_json(analysis_dir / "btc_1d_post_spike_entry_shape_idle_repair_batch_latest.json")
    followup_batch = _load_json(analysis_dir / "btc_1d_post_spike_idle_window_followup_batch_latest.json")

    stage3_best = dict(stage3_batch["best_variant"])
    entry_anchor = _load_variant_from_batch(
        analysis_dir / "btc_1d_post_spike_entry_shape_idle_repair_batch_latest.json",
        "anchor_entry_shape",
    )
    faster_trigger = _load_variant_from_batch(
        analysis_dir / "btc_1d_post_spike_entry_shape_idle_repair_batch_latest.json",
        "faster_trigger_entry_shape",
    )
    trend9504 = _load_variant_from_batch(
        analysis_dir / "btc_1d_post_spike_idle_window_followup_batch_latest.json",
        "trend9504_depth055_volume104_hold36",
    )
    slower_confirmation = _load_variant_from_batch(
        analysis_dir / "btc_1d_post_spike_entry_shape_idle_repair_batch_latest.json",
        "deeper_confirmation_entry_shape",
    )

    variant_specs = [
        ("repair_anchor_best", stage3_best),
        ("entry_anchor", entry_anchor),
        ("faster_trigger_entry_shape", faster_trigger),
        ("high_cagr_trend9504", trend9504),
        ("slower_confirmation_entry_shape", slower_confirmation),
    ]

    compared_variants: list[dict] = []
    for role, row in variant_specs:
        diagnostic = _load_json(analysis_dir / Path(str(row["analysis_result_json"])).name)
        window2 = _window_summary(diagnostic, target_window=2)
        compared_variants.append(
            {
                "role": role,
                "variant_label": str(row["variant_label"]),
                "base_cagr": float(row.get("base_cagr", 0.0)),
                "base_sharpe": float(row.get("base_sharpe", 0.0)),
                "sensitivity_max_drift": float(row.get("sensitivity_max_drift", 0.0)),
                "negative_windows": list(row.get("negative_windows", [])),
                "idle_windows": list(row.get("idle_windows", [])),
                "window_2": window2,
            }
        )

    reference = compared_variants[0]["window_2"]
    repeated_idle_roles = [
        variant["role"]
        for variant in compared_variants
        if variant["window_2"]["trades"] == reference["trades"]
        and variant["window_2"]["equity_end"] == reference["equity_end"]
        and variant["window_2"]["timestamp_start"] == reference["timestamp_start"]
        and variant["window_2"]["timestamp_end"] == reference["timestamp_end"]
    ]

    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "window_2_reference": reference,
        "compared_variants": compared_variants,
        "idle_window_context_verdict": {
            "window_2_is_structurally_idle_across_current_axes": len(repeated_idle_roles) >= 4,
            "repeated_idle_roles": repeated_idle_roles,
            "next_axis_now": "open_trade_formation_or_regime_gate_axis",
            "reason": (
                "Window 2 keeps the same zero-trade signature across the repair anchor, "
                "entry-shape anchor, faster-trigger entry shape, and the high-CAGR trend9504 variant, "
                "which indicates the current hold/shape micro-axes are not changing trade formation in that regime."
            ),
        },
    }


def _render_markdown(report: dict) -> str:
    lines = [
        "# BTC 1d Post-Spike Idle Window Context",
        "",
        f"- Window 2 start: `{report['window_2_reference']['timestamp_start']}`",
        f"- Window 2 end: `{report['window_2_reference']['timestamp_end']}`",
        f"- Window 2 trades: `{report['window_2_reference']['trades']}`",
        f"- Window 2 equity end: `{report['window_2_reference']['equity_end']:.4f}`",
        f"- Structurally idle across current axes: `{report['idle_window_context_verdict']['window_2_is_structurally_idle_across_current_axes']}`",
        f"- Repeated idle roles: `{report['idle_window_context_verdict']['repeated_idle_roles']}`",
        f"- Next axis now: `{report['idle_window_context_verdict']['next_axis_now']}`",
        f"- Reason: {report['idle_window_context_verdict']['reason']}",
        "",
        "## Compared Variants",
    ]
    for row in report["compared_variants"]:
        window2 = row["window_2"]
        lines.append(
            f"- `{row['role']}` | `{row['variant_label']}` | base_cagr=`{row['base_cagr']:.4f}` | drift=`{row['sensitivity_max_drift']:.4f}` | idle_windows=`{row['idle_windows']}` | window2_trades=`{window2['trades']}` | window2_range=`{window2['timestamp_start']}` -> `{window2['timestamp_end']}`"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_post_spike_idle_window_context_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_post_spike_idle_window_context_{stamp}.md"
    latest_json = ANALYSIS_DIR / "btc_1d_post_spike_idle_window_context_latest.json"
    latest_md = ANALYSIS_DIR / "btc_1d_post_spike_idle_window_context_md_latest.md"
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
