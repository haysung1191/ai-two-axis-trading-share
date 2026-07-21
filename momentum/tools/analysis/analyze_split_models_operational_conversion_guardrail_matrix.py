from __future__ import annotations

import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_guardrail_matrix"

REDISTRIBUTION_SWEEP_JSON = (
    ROOT / "output" / "split_models_operational_conversion_redistribution_sweep" / "redistribution_sweep_summary.json"
)
SYMBOL_CAP_SWEEP_JSON = (
    ROOT / "output" / "split_models_operational_conversion_symbol_cap_sweep" / "symbol_cap_sweep_summary.json"
)
SOFTFLOW_GUARD_SWEEP_JSON = (
    ROOT / "output" / "split_models_operational_conversion_softflow_guard_sweep" / "softflow_guard_sweep_summary.json"
)
SECTOR_GUARD_SWEEP_JSON = (
    ROOT / "output" / "split_models_operational_conversion_sector_guard_sweep" / "sector_guard_sweep_summary.json"
)
TAILCOUNT_GUARD_SWEEP_JSON = (
    ROOT / "output" / "split_models_operational_conversion_tailcount_guard_sweep" / "tailcount_guard_sweep_summary.json"
)
TARGETED_TRIM_SWEEP_JSON = (
    ROOT / "output" / "split_models_operational_conversion_targeted_trim_sweep" / "targeted_trim_sweep_summary.json"
)
KR_ETF_GUARD_SWEEP_JSON = (
    ROOT / "output" / "split_models_operational_conversion_kr_etf_guard_sweep" / "kr_etf_guard_sweep_summary.json"
)
FALLBACK_SWEEP_JSON = (
    ROOT / "output" / "split_models_operational_conversion_fallback_sweep" / "fallback_sweep_summary.json"
)
DEFENSIVE_RECIPIENTS_SWEEP_JSON = (
    ROOT / "output" / "split_models_operational_conversion_defensive_recipients_sweep" / "defensive_recipients_sweep_summary.json"
)
US_SLEEVE_GUARD_SWEEP_JSON = (
    ROOT / "output" / "split_models_operational_conversion_us_sleeve_guard_sweep" / "us_sleeve_guard_sweep_summary.json"
)
CASH_BUFFER_SWEEP_JSON = (
    ROOT / "output" / "split_models_operational_conversion_cash_buffer_sweep" / "cash_buffer_sweep_summary.json"
)
CONCENTRATED_BOOK_SWEEP_JSON = (
    ROOT / "output" / "split_models_operational_conversion_concentrated_book_sweep" / "concentrated_book_sweep_summary.json"
)
BASELINE_SWITCH_CARRY_SWEEP_JSON = (
    ROOT / "output" / "split_models_operational_conversion_baseline_switch_carry_sweep" / "baseline_switch_carry_sweep_summary.json"
)
CONCENTRATION_TRIGGER_SWEEP_JSON = (
    ROOT / "output" / "split_models_operational_conversion_concentration_trigger_sweep" / "concentration_trigger_sweep_summary.json"
)
CONCENTRATION_CARRY_BRIDGE_SWEEP_JSON = (
    ROOT / "output" / "split_models_operational_conversion_concentration_carry_bridge_sweep" / "concentration_carry_bridge_sweep_summary.json"
)
CONCENTRATION_CARRY_THRESHOLD_REFINE_JSON = (
    ROOT / "output" / "split_models_operational_conversion_concentration_carry_threshold_refine" / "concentration_carry_threshold_refine_summary.json"
)
CONCENTRATION_CARRY_RECIPIENT_SWEEP_JSON = (
    ROOT / "output" / "split_models_operational_conversion_concentration_carry_recipient_sweep" / "concentration_carry_recipient_sweep_summary.json"
)
CONCENTRATION_CARRY_KR_ETF_TRIM_REFINE_JSON = (
    ROOT / "output" / "split_models_operational_conversion_concentration_carry_kr_etf_trim_refine" / "concentration_carry_kr_etf_trim_refine_summary.json"
)
CONCENTRATION_CARRY_KR_ETF_TRIM_MICRO_JSON = (
    ROOT / "output" / "split_models_operational_conversion_concentration_carry_kr_etf_trim_micro" / "concentration_carry_kr_etf_trim_micro_summary.json"
)
CONCENTRATION_CARRY_KR_ETF_IT_EXCEPTION_JSON = (
    ROOT / "output" / "split_models_operational_conversion_concentration_carry_kr_etf_it_exception_sweep" / "concentration_carry_kr_etf_it_exception_sweep_summary.json"
)
SINGLE_NAME_TRIGGER_TRIM_REFINE_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_single_name_trigger_trim_refine"
    / "single_name_trigger_trim_refine_summary.json"
)

BASE_VARIANT = "tail_release_top25_mid75_pen35_floor25"
BASE_MDD = -0.3383321870730238
BASE_CAGR = 0.7479958086653411
BASE_SHARPE = 1.6936987997817152
BASELINE_MDD = -0.2524158832009178


def _pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _axis_row(
    *,
    axis: str,
    summary: dict,
    variant_key: str,
    cagr_key: str,
    mdd_key: str,
    sharpe_key: str,
) -> dict[str, object]:
    cagr = float(summary[cagr_key])
    mdd = float(summary[mdd_key])
    sharpe = float(summary[sharpe_key])
    mdd_delta = mdd - BASE_MDD
    cagr_delta = cagr - BASE_CAGR
    sharpe_delta = sharpe - BASE_SHARPE

    classification = "quality_up_same_drawdown"
    if abs(mdd_delta) < 1e-12 and abs(cagr_delta) < 1e-12 and abs(sharpe_delta) < 1e-12:
        classification = "no_op"
    elif mdd_delta > 0:
        classification = "drawdown_improved"
    elif cagr_delta < 0 and sharpe_delta < 0:
        classification = "worse"

    return {
        "axis": axis,
        "best_variant": str(summary[variant_key]),
        "classification": classification,
        "cagr": cagr,
        "mdd": mdd,
        "sharpe": sharpe,
        "cagr_delta_vs_base": cagr_delta,
        "mdd_delta_vs_base": mdd_delta,
        "sharpe_delta_vs_base": sharpe_delta,
        "verdict": str(summary["verdict"]),
    }


def _build_markdown(rows: list[dict[str, object]]) -> str:
    quality_rows = [row for row in rows if row["classification"] == "quality_up_same_drawdown"]
    best_quality = max(quality_rows, key=lambda row: (row["sharpe_delta_vs_base"], row["cagr_delta_vs_base"])) if quality_rows else None
    drawdown_improvers = [row for row in rows if row["mdd_delta_vs_base"] > 1e-12]

    lines = [
        "# Split Models Operational Conversion Guardrail Matrix",
        "",
        "## Purpose",
        "",
        "- compress the recent operating-conversion axis search into one matrix",
        "- separate true drawdown repair from quality-only improvement, failure, and no-op axes",
        "",
        "## Base Point",
        "",
        f"- current base point: `{BASE_VARIANT}`",
        f"- CAGR: `{_pct(BASE_CAGR)}`",
        f"- MDD: `{_pct(BASE_MDD)}`",
        f"- Sharpe: `{BASE_SHARPE:.4f}`",
        f"- remaining drawdown gap vs operating baseline: `{_pct(BASE_MDD - BASELINE_MDD)}`",
        "",
        "## Axis Matrix",
        "",
        "| Axis | Best Variant | Classification | CAGR delta | MDD delta | Sharpe delta |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]

    for row in rows:
        lines.append(
            f"| `{row['axis']}` | `{row['best_variant']}` | `{row['classification']}` | "
            f"{_pct(row['cagr_delta_vs_base'])} | {_pct(row['mdd_delta_vs_base'])} | {row['sharpe_delta_vs_base']:+.4f} |"
        )

    lines.extend(
        [
            "",
            "## Read",
            "",
            f"- best quality-improving axis so far: `{best_quality['axis']}` via `{best_quality['best_variant']}`" if best_quality else "- best quality-improving axis so far: `none`",
            f"- drawdown-improving axes found: `{len(drawdown_improvers)}`",
        ]
    )

    if drawdown_improvers:
        for row in drawdown_improvers:
            lines.append(
                f"- `{row['axis']}` improves MDD by {_pct(row['mdd_delta_vs_base'])} versus base"
            )
    else:
        lines.append("- no tested axis has improved MDD versus the current base point yet")

    lines.extend(
        [
            "",
            "## Verdict",
            "",
            (
                f"- the current search has produced `{len(drawdown_improvers)}` true drawdown-repair axis/axes"
                if drawdown_improvers
                else "- the current search has produced zero true drawdown-repair axes"
            ),
            f"- keep `{BASE_VARIANT}` as the drawdown-control anchor for now",
            f"- treat `{best_quality['best_variant']}` as the current best quality overlay, not a drawdown solution" if best_quality else "- there is no quality overlay leader yet",
            "- stop retrying the explicit no-op / failed axes and only search genuinely new drawdown-repair structures next",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = [
        _axis_row(
            axis="redistribution_sweep",
            summary=_load_json(REDISTRIBUTION_SWEEP_JSON),
            variant_key="best_drawdown_control_variant",
            cagr_key="best_drawdown_control_cagr",
            mdd_key="best_drawdown_control_mdd",
            sharpe_key="best_drawdown_control_sharpe",
        ),
        _axis_row(
            axis="symbol_cap",
            summary=_load_json(SYMBOL_CAP_SWEEP_JSON),
            variant_key="best_cap_variant",
            cagr_key="best_cap_cagr",
            mdd_key="best_cap_mdd",
            sharpe_key="best_cap_sharpe",
        ),
        _axis_row(
            axis="softflow_guard",
            summary=_load_json(SOFTFLOW_GUARD_SWEEP_JSON),
            variant_key="best_variant",
            cagr_key="best_cagr",
            mdd_key="best_mdd",
            sharpe_key="best_sharpe",
        ),
        _axis_row(
            axis="sector_guard",
            summary=_load_json(SECTOR_GUARD_SWEEP_JSON),
            variant_key="best_variant",
            cagr_key="best_cagr",
            mdd_key="best_mdd",
            sharpe_key="best_sharpe",
        ),
        _axis_row(
            axis="tailcount_guard",
            summary=_load_json(TAILCOUNT_GUARD_SWEEP_JSON),
            variant_key="best_variant",
            cagr_key="best_cagr",
            mdd_key="best_mdd",
            sharpe_key="best_sharpe",
        ),
        _axis_row(
            axis="targeted_trim",
            summary=_load_json(TARGETED_TRIM_SWEEP_JSON),
            variant_key="best_variant",
            cagr_key="best_cagr",
            mdd_key="best_mdd",
            sharpe_key="best_sharpe",
        ),
        _axis_row(
            axis="kr_etf_guard",
            summary=_load_json(KR_ETF_GUARD_SWEEP_JSON),
            variant_key="best_variant",
            cagr_key="best_cagr",
            mdd_key="best_mdd",
            sharpe_key="best_sharpe",
        ),
        _axis_row(
            axis="fallback",
            summary=_load_json(FALLBACK_SWEEP_JSON),
            variant_key="best_variant",
            cagr_key="best_cagr",
            mdd_key="best_mdd",
            sharpe_key="best_sharpe",
        ),
        _axis_row(
            axis="defensive_recipients",
            summary=_load_json(DEFENSIVE_RECIPIENTS_SWEEP_JSON),
            variant_key="best_variant",
            cagr_key="best_cagr",
            mdd_key="best_mdd",
            sharpe_key="best_sharpe",
        ),
        _axis_row(
            axis="us_sleeve_guard",
            summary=_load_json(US_SLEEVE_GUARD_SWEEP_JSON),
            variant_key="best_variant",
            cagr_key="best_cagr",
            mdd_key="best_mdd",
            sharpe_key="best_sharpe",
        ),
        _axis_row(
            axis="cash_buffer",
            summary=_load_json(CASH_BUFFER_SWEEP_JSON),
            variant_key="best_variant",
            cagr_key="best_cagr",
            mdd_key="best_mdd",
            sharpe_key="best_sharpe",
        ),
        _axis_row(
            axis="concentrated_book",
            summary=_load_json(CONCENTRATED_BOOK_SWEEP_JSON),
            variant_key="best_variant",
            cagr_key="best_cagr",
            mdd_key="best_mdd",
            sharpe_key="best_sharpe",
        ),
        _axis_row(
            axis="baseline_switch_carry",
            summary=_load_json(BASELINE_SWITCH_CARRY_SWEEP_JSON),
            variant_key="best_variant",
            cagr_key="best_cagr",
            mdd_key="best_mdd",
            sharpe_key="best_sharpe",
        ),
        _axis_row(
            axis="concentration_trigger",
            summary=_load_json(CONCENTRATION_TRIGGER_SWEEP_JSON),
            variant_key="best_variant",
            cagr_key="best_cagr",
            mdd_key="best_mdd",
            sharpe_key="best_sharpe",
        ),
        _axis_row(
            axis="concentration_carry_bridge",
            summary=_load_json(CONCENTRATION_CARRY_BRIDGE_SWEEP_JSON),
            variant_key="best_variant",
            cagr_key="best_cagr",
            mdd_key="best_mdd",
            sharpe_key="best_sharpe",
        ),
        _axis_row(
            axis="concentration_carry_threshold_refine",
            summary=_load_json(CONCENTRATION_CARRY_THRESHOLD_REFINE_JSON),
            variant_key="best_variant",
            cagr_key="best_cagr",
            mdd_key="best_mdd",
            sharpe_key="best_sharpe",
        ),
        _axis_row(
            axis="concentration_carry_recipient",
            summary=_load_json(CONCENTRATION_CARRY_RECIPIENT_SWEEP_JSON),
            variant_key="best_variant",
            cagr_key="best_cagr",
            mdd_key="best_mdd",
            sharpe_key="best_sharpe",
        ),
        _axis_row(
            axis="concentration_carry_kr_etf_trim_refine",
            summary=_load_json(CONCENTRATION_CARRY_KR_ETF_TRIM_REFINE_JSON),
            variant_key="best_variant",
            cagr_key="best_cagr",
            mdd_key="best_mdd",
            sharpe_key="best_sharpe",
        ),
        _axis_row(
            axis="concentration_carry_kr_etf_trim_micro",
            summary=_load_json(CONCENTRATION_CARRY_KR_ETF_TRIM_MICRO_JSON),
            variant_key="best_variant",
            cagr_key="best_cagr",
            mdd_key="best_mdd",
            sharpe_key="best_sharpe",
        ),
        _axis_row(
            axis="concentration_carry_kr_etf_it_exception",
            summary=_load_json(CONCENTRATION_CARRY_KR_ETF_IT_EXCEPTION_JSON),
            variant_key="best_variant",
            cagr_key="best_cagr",
            mdd_key="best_mdd",
            sharpe_key="best_sharpe",
        ),
        _axis_row(
            axis="single_name_trigger",
            summary=_load_json(SINGLE_NAME_TRIGGER_TRIM_REFINE_JSON),
            variant_key="best_variant",
            cagr_key="best_cagr",
            mdd_key="best_mdd",
            sharpe_key="best_sharpe",
        ),
    ]

    rows = sorted(rows, key=lambda row: (row["mdd_delta_vs_base"], row["sharpe_delta_vs_base"], row["cagr_delta_vs_base"]), reverse=True)

    quality_rows = [row for row in rows if row["classification"] == "quality_up_same_drawdown"]
    best_quality = max(quality_rows, key=lambda row: (row["sharpe_delta_vs_base"], row["cagr_delta_vs_base"])) if quality_rows else None

    summary = {
        "base_variant": BASE_VARIANT,
        "base_cagr": BASE_CAGR,
        "base_mdd": BASE_MDD,
        "base_sharpe": BASE_SHARPE,
        "baseline_mdd": BASELINE_MDD,
        "drawdown_improver_count": sum(1 for row in rows if row["mdd_delta_vs_base"] > 1e-12),
        "quality_up_same_drawdown_count": sum(1 for row in rows if row["classification"] == "quality_up_same_drawdown"),
        "no_op_count": sum(1 for row in rows if row["classification"] == "no_op"),
        "worse_count": sum(1 for row in rows if row["classification"] == "worse"),
        "best_quality_axis": None if best_quality is None else best_quality["axis"],
        "best_quality_variant": None if best_quality is None else best_quality["best_variant"],
        "rows": rows,
        "verdict": (
            (
                f"the search now has `{sum(1 for row in rows if row['mdd_delta_vs_base'] > 1e-12)}` drawdown-improving axis/axes; "
                f"the strongest same-drawdown quality overlay is `{best_quality['best_variant']}` from `{best_quality['axis']}`"
            )
            if best_quality is not None and any(row["mdd_delta_vs_base"] > 1e-12 for row in rows)
            else (
                "no tested operating-conversion axis has improved drawdown versus the current redistribution base; "
                f"the best recent progress is quality improvement at the same drawdown level, currently led by "
                f"`{best_quality['best_variant']}` from `{best_quality['axis']}`"
            )
            if best_quality is not None
            else "no tested operating-conversion axis has improved drawdown versus the current redistribution base"
        ),
    }

    (OUTPUT_DIR / "guardrail_matrix_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "guardrail_matrix.md").write_text(_build_markdown(rows), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
