from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_drawdown_window_defense_validation"
DEFENSE_SUMMARY = (
    ROOT
    / "output"
    / "split_models_operational_conversion_drawdown_window_defense_sweep"
    / "drawdown_window_defense_sweep_summary.json"
)
BASELINE_MDD = -0.25241596238415986
MIN_CAGR = 0.50
MIN_SHARPE = 1.50


def _pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _best_row(summary: dict) -> dict:
    variant = summary["best_variant"]
    for row in summary["ranked_rows"]:
        if row.get("Variant") == variant:
            return row
    raise KeyError(f"best variant row not found: {variant}")


def _build_markdown(report: dict) -> str:
    checks = "\n".join(
        f"- `{row['id']}`: {'PASS' if row['passed'] else 'BLOCK'}; observed `{row['observed']}`"
        for row in report["checklist"]
    )
    return f"""# Drawdown Window Defense Validation Audit

Generated: `{report['generated_at']}`

## Decision

`{report['validation_decision']}`

## Candidate

- Variant: `{report['candidate']['variant']}`
- CAGR: `{_pct(report['candidate']['cagr'])}`
- MDD: `{_pct(report['candidate']['mdd'])}`
- Sharpe: `{report['candidate']['sharpe']:.4f}`
- MDD margin vs operating baseline: `{_pct(report['candidate']['mdd_margin_vs_operating_baseline'])}`

## Checklist

{checks}

## Promotion Note

{report['promotion_note']}
"""


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = _load_json(DEFENSE_SUMMARY)
    best = _best_row(summary)
    cagr = float(summary["best_cagr"])
    mdd = float(summary["best_mdd"])
    sharpe = float(summary["best_sharpe"])
    mdd_margin = mdd - BASELINE_MDD
    checklist = [
        {
            "id": "mdd_beats_operating_baseline",
            "passed": mdd > BASELINE_MDD,
            "observed": {
                "candidate_mdd": mdd,
                "operating_baseline_mdd": BASELINE_MDD,
                "margin": mdd_margin,
            },
        },
        {
            "id": "cagr_remains_growth_grade",
            "passed": cagr >= MIN_CAGR,
            "observed": {"candidate_cagr": cagr, "minimum_cagr": MIN_CAGR},
        },
        {
            "id": "sharpe_remains_quality_grade",
            "passed": sharpe >= MIN_SHARPE,
            "observed": {"candidate_sharpe": sharpe, "minimum_sharpe": MIN_SHARPE},
        },
        {
            "id": "walkforward_non_negative",
            "passed": int(best.get("NegativeCAGRWindows") or 0) == 0,
            "observed": {
                "positive_cagr_windows": int(best.get("PositiveCAGRWindows") or 0),
                "negative_cagr_windows": int(best.get("NegativeCAGRWindows") or 0),
            },
        },
        {
            "id": "cost_sensitivity_positive",
            "passed": float(best.get("Cost75BpsCAGRDelta") or 0.0) > 0.0
            and float(best.get("Cost75BpsSharpeDelta") or 0.0) > 0.0,
            "observed": {
                "cost75bps_cagr_delta": float(best.get("Cost75BpsCAGRDelta") or 0.0),
                "cost75bps_sharpe_delta": float(best.get("Cost75BpsSharpeDelta") or 0.0),
            },
        },
    ]
    validation_passed = all(row["passed"] for row in checklist)
    report = {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_summary": str(DEFENSE_SUMMARY),
        "validation_decision": "PASS_FIRST_ORDER_METRIC_VALIDATION" if validation_passed else "BLOCK_METRIC_VALIDATION",
        "candidate": {
            "variant": summary["best_variant"],
            "cagr": cagr,
            "mdd": mdd,
            "sharpe": sharpe,
            "mdd_margin_vs_operating_baseline": mdd_margin,
            "window_start": summary["window_start"],
            "window_end": summary["window_end"],
            "weak_switch_count": int(summary["best_weak_switch_count"]),
            "window_defense_count": int(summary["best_window_defense_count"]),
        },
        "checklist": checklist,
        "promotion_note": (
            "This closes the current MDD bottleneck on first-order backtest metrics. Because the rule is explicitly "
            "drawdown-window-scoped, it is not sufficient by itself for live or broker promotion; it should next be "
            "registered as a conversion candidate and tested with OOS/robustness gates."
        ),
    }
    latest_json = OUTPUT_DIR / "drawdown_window_defense_validation_latest.json"
    latest_md = OUTPUT_DIR / "drawdown_window_defense_validation_latest.md"
    latest_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    latest_md.write_text(_build_markdown(report), encoding="utf-8")
    print(json.dumps({"validation_decision": report["validation_decision"], "latest_json": str(latest_json)}, indent=2))


if __name__ == "__main__":
    main()
