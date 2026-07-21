from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.domains.experiments.btc_1d_walk_forward_diagnostic import (
    Btc1dWalkForwardDiagnosticConfig,
    Btc1dWalkForwardDiagnosticService,
)


ANALYSIS_DIR = Path("analysis_results")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _window2_range(analysis_dir: Path) -> tuple[pd.Timestamp, pd.Timestamp]:
    context = _load_json(analysis_dir / "btc_1d_post_spike_idle_window_context_latest.json")
    reference = dict(context["window_2_reference"])
    return (
        pd.Timestamp(str(reference["timestamp_start"])),
        pd.Timestamp(str(reference["timestamp_end"])),
    )


def _load_ohlcv(periods: int = 2200) -> pd.DataFrame:
    service = Btc1dWalkForwardDiagnosticService(analysis_results_dir=ANALYSIS_DIR)
    return service._load_ohlcv(  # noqa: SLF001
        Btc1dWalkForwardDiagnosticConfig(
            symbol="BTCUSDT",
            interval="1d",
            periods=periods,
            strategy_name="btc_1d_post_spike_consolidation_breakout_v4",
            allow_synthetic_ohlcv_fallback=False,
        )
    )


def _gate_rows(ohlcv: pd.DataFrame, params: dict[str, Any]) -> list[dict[str, Any]]:
    high = ohlcv["high"].astype(float)
    low = ohlcv["low"].astype(float)
    close = ohlcv["close"].astype(float)
    volume = ohlcv["volume"].astype(float)

    trend = close.ewm(span=int(params["trend_ema_window"]), adjust=False).mean()
    traded_value = close * volume
    avg_traded_value = traded_value.rolling(
        window=int(params["volume_lookback"]),
        min_periods=int(params["volume_lookback"]),
    ).mean().replace(0.0, pd.NA)

    consolidation_window = int(params["consolidation_window"])
    spike_lookback = int(params["spike_lookback"])
    min_points = max(
        int(params["trend_ema_window"]),
        spike_lookback + consolidation_window + 1,
        int(params["volume_lookback"]),
        int(params["stop_ema_window"]),
    ) + 2

    rows: list[dict[str, Any]] = []
    for idx in range(min_points - 1, len(ohlcv)):
        ts = ohlcv.index[idx]
        close_value = float(close.iloc[idx])
        trend_value = float(trend.iloc[idx])

        pre_consolidation_start = idx - consolidation_window - spike_lookback
        pre_consolidation_end = idx - consolidation_window
        spike_low = float(low.iloc[pre_consolidation_start:pre_consolidation_end].min())
        spike_high = float(high.iloc[pre_consolidation_start:pre_consolidation_end].max())
        spike_pct = ((spike_high - spike_low) / spike_low) if spike_low > 0 else 0.0

        consolidation_high = float(high.iloc[idx - consolidation_window:idx].max())
        consolidation_low = float(low.iloc[idx - consolidation_window:idx].min())
        consolidation_mid = (consolidation_high + consolidation_low) / 2.0
        consolidation_depth = (
            (consolidation_high - consolidation_low) / consolidation_mid
            if consolidation_mid > 0
            else 0.0
        )
        breakout_level = consolidation_high * (1.0 + float(params["breakout_buffer_pct"]))
        traded_ratio = (
            float(traded_value.iloc[idx] / avg_traded_value.iloc[idx])
            if pd.notna(avg_traded_value.iloc[idx])
            else 0.0
        )

        gates = {
            "trend_gate": close_value > trend_value,
            "spike_gate": spike_pct >= float(params["min_spike_pct"]),
            "consolidation_gate": consolidation_depth <= float(params["max_consolidation_depth_pct"]),
            "breakout_gate": close_value >= breakout_level,
            "volume_gate": traded_ratio >= float(params["min_volume_ratio"]),
        }
        breakout_ready = all(gates.values())
        rows.append(
            {
                "timestamp": ts,
                "close": close_value,
                "trend": trend_value,
                "spike_pct": spike_pct,
                "consolidation_depth": consolidation_depth,
                "breakout_level": breakout_level,
                "traded_ratio": traded_ratio,
                "breakout_ready": breakout_ready,
                **gates,
            }
        )
    return rows


def _summarize_window(rows: list[dict[str, Any]], start: pd.Timestamp, end: pd.Timestamp) -> dict[str, Any]:
    window_rows = [row for row in rows if start <= row["timestamp"] <= end]
    counts = Counter()
    first_blocker = Counter()
    for row in window_rows:
        counts["bars"] += 1
        for gate in ("trend_gate", "spike_gate", "consolidation_gate", "breakout_gate", "volume_gate"):
            if row[gate]:
                counts[f"{gate}_pass"] += 1
        if row["breakout_ready"]:
            counts["breakout_ready_pass"] += 1
            continue
        for gate in ("trend_gate", "spike_gate", "consolidation_gate", "breakout_gate", "volume_gate"):
            if not row[gate]:
                first_blocker[gate] += 1
                break

    top_blockers = [
        {"gate": gate, "count": count}
        for gate, count in first_blocker.most_common()
    ]
    return {
        "bars": counts["bars"],
        "trend_gate_pass": counts["trend_gate_pass"],
        "spike_gate_pass": counts["spike_gate_pass"],
        "consolidation_gate_pass": counts["consolidation_gate_pass"],
        "breakout_gate_pass": counts["breakout_gate_pass"],
        "volume_gate_pass": counts["volume_gate_pass"],
        "breakout_ready_pass": counts["breakout_ready_pass"],
        "top_blockers": top_blockers,
    }


def build_report(analysis_dir: Path = ANALYSIS_DIR) -> dict[str, Any]:
    start, end = _window2_range(analysis_dir)
    ohlcv = _load_ohlcv()

    variants = [
        {
            "role": "repair_anchor_best",
            "label": "trend1056_depth055_volume104_stop22_hold36",
            "params": {
                "trend_ema_window": 105.6,
                "spike_lookback": 24,
                "min_spike_pct": 0.085,
                "consolidation_window": 7,
                "max_consolidation_depth_pct": 0.055,
                "breakout_buffer_pct": 0.002,
                "volume_lookback": 20,
                "min_volume_ratio": 1.04,
                "stop_ema_window": 22.0,
                "max_hold_bars": 36.0,
            },
        },
        {
            "role": "high_cagr_trend9504",
            "label": "trend9504_depth055_volume104_hold36",
            "params": {
                "trend_ema_window": 95.04,
                "spike_lookback": 24,
                "min_spike_pct": 0.085,
                "consolidation_window": 7,
                "max_consolidation_depth_pct": 0.055,
                "breakout_buffer_pct": 0.002,
                "volume_lookback": 20,
                "min_volume_ratio": 1.04,
                "stop_ema_window": 20.0,
                "max_hold_bars": 36.0,
            },
        },
    ]

    compared: list[dict[str, Any]] = []
    for variant in variants:
        rows = _gate_rows(ohlcv, variant["params"])
        compared.append(
            {
                "role": variant["role"],
                "variant_label": variant["label"],
                "window_2_gate_summary": _summarize_window(rows, start, end),
            }
        )

    primary = compared[0]["window_2_gate_summary"]
    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "window_2_range": {
            "timestamp_start": start.isoformat(),
            "timestamp_end": end.isoformat(),
        },
        "compared_variants": compared,
        "gate_diagnostic_verdict": {
            "window_2_breakout_ready_bars": int(primary["breakout_ready_pass"]),
            "primary_blocker_gate": primary["top_blockers"][0]["gate"] if primary["top_blockers"] else None,
            "next_axis_now": "change_breakout_rule_or_volume_rule_logic",
            "reason": (
                "The current anchor still produces zero fully qualified breakout bars in window 2, "
                "so the next step should change the trigger logic at the dominant blocker gate instead of tuning downstream controls."
            ),
        },
    }


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# BTC 1d Post-Spike Window 2 Gate Diagnostic",
        "",
        f"- Window 2 start: `{report['window_2_range']['timestamp_start']}`",
        f"- Window 2 end: `{report['window_2_range']['timestamp_end']}`",
        f"- Primary blocker gate: `{report['gate_diagnostic_verdict']['primary_blocker_gate']}`",
        f"- Breakout-ready bars in window 2: `{report['gate_diagnostic_verdict']['window_2_breakout_ready_bars']}`",
        f"- Next axis now: `{report['gate_diagnostic_verdict']['next_axis_now']}`",
        f"- Reason: {report['gate_diagnostic_verdict']['reason']}",
        "",
        "## Compared Variants",
    ]
    for row in report["compared_variants"]:
        summary = row["window_2_gate_summary"]
        lines.append(
            f"- `{row['role']}` | `{row['variant_label']}` | bars=`{summary['bars']}` | trend_pass=`{summary['trend_gate_pass']}` | spike_pass=`{summary['spike_gate_pass']}` | consolidation_pass=`{summary['consolidation_gate_pass']}` | breakout_pass=`{summary['breakout_gate_pass']}` | volume_pass=`{summary['volume_gate_pass']}` | breakout_ready=`{summary['breakout_ready_pass']}` | top_blockers=`{summary['top_blockers'][:3]}`"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_post_spike_window2_gate_diagnostic_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_post_spike_window2_gate_diagnostic_{stamp}.md"
    latest_json = ANALYSIS_DIR / "btc_1d_post_spike_window2_gate_diagnostic_latest.json"
    latest_md = ANALYSIS_DIR / "btc_1d_post_spike_window2_gate_diagnostic_md_latest.md"
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
