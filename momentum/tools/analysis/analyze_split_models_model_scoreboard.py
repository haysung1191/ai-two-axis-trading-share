from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "output"
SCOREBOARD_DIR = OUTPUT_DIR / "split_models_model_scoreboard"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _collect_variant_strings(payload: object, *, key_name: str | None = None) -> set[str]:
    variants: set[str] = set()
    if isinstance(payload, dict):
        for child_key, child_value in payload.items():
            variants.update(_collect_variant_strings(child_value, key_name=str(child_key)))
    elif isinstance(payload, list):
        for item in payload:
            variants.update(_collect_variant_strings(item, key_name=key_name))
    elif isinstance(payload, str):
        normalized_key = (key_name or "").lower()
        if normalized_key in {
            "variant",
            "best_variant",
            "baseline_variant",
            "aggressive_strongest_variant",
            "anchor_variant",
            "recommended_representative_variant",
            "recommended_variant",
            "growth_variant",
            "drawdown_variant",
            "balance_variant",
            "best_quality_variant",
        }:
            variants.add(payload)
    return variants


def _load_metric_lookup() -> dict[str, dict[str, object]]:
    lookup: dict[str, dict[str, object]] = {}

    candidates_payload = _read_json(
        OUTPUT_DIR / "split_models_operational_conversion_candidates" / "operational_conversion_candidates_summary.json"
    )
    baseline_metrics = candidates_payload["baseline_metrics"]
    lookup[candidates_payload["baseline_variant"]] = {
        "variant": candidates_payload["baseline_variant"],
        "role": "operating_baseline",
        "cagr": baseline_metrics["cagr"],
        "mdd": baseline_metrics["mdd"],
        "sharpe": baseline_metrics["sharpe"],
        "annual_turnover": baseline_metrics.get("annual_turnover"),
        "cost_metric": None,
        "negative_walk_forward_windows": None,
        "note": "production baseline",
    }

    reference_row = candidates_payload["reference_row"]
    lookup[reference_row["variant"]] = {
        "variant": reference_row["variant"],
        "role": "aggressive_strongest",
        "cagr": reference_row["cagr"],
        "mdd": reference_row["mdd"],
        "sharpe": reference_row["sharpe"],
        "annual_turnover": reference_row.get("annual_turnover"),
        "cost_metric": reference_row.get("cost_75bps_cagr_delta_vs_strongest"),
        "negative_walk_forward_windows": reference_row.get("negative_cagr_windows"),
        "note": "current strongest reference",
    }

    for row in candidates_payload.get("rows", []):
        lookup[row["variant"]] = {
            "variant": row["variant"],
            "role": row.get("conversion_grade", "candidate"),
            "cagr": row["cagr"],
            "mdd": row["mdd"],
            "sharpe": row["sharpe"],
            "annual_turnover": row.get("annual_turnover"),
            "cost_metric": row.get("cost_75bps_cagr_delta_vs_strongest"),
            "negative_walk_forward_windows": row.get("negative_cagr_windows"),
            "note": "; ".join(row.get("notes", [])),
        }

    guardrail_payload = _read_json(
        OUTPUT_DIR / "split_models_operational_conversion_guardrail_matrix" / "guardrail_matrix_summary.json"
    )
    for row in guardrail_payload.get("rows", []):
        lookup[row["best_variant"]] = {
            "variant": row["best_variant"],
            "role": row.get("classification", "guardrail_variant"),
            "cagr": row["cagr"],
            "mdd": row["mdd"],
            "sharpe": row["sharpe"],
            "annual_turnover": None,
            "cost_metric": None,
            "negative_walk_forward_windows": None,
            "note": row.get("axis"),
        }

    promotion_payload = _read_json(
        OUTPUT_DIR
        / "split_models_operational_conversion_promotion_recommendation"
        / "promotion_recommendation_summary.json"
    )
    for row in promotion_payload.get("rows", []):
        lookup[row["variant"]] = {
            "variant": row["variant"],
            "role": f"promotion_{row.get('role', 'candidate')}",
            "cagr": row["cagr"],
            "mdd": row["mdd"],
            "sharpe": row["sharpe"],
            "annual_turnover": None,
            "cost_metric": None,
            "negative_walk_forward_windows": None,
            "note": f"trim_fraction={row.get('trim_fraction')}",
        }

    return lookup


def build_payload() -> dict[str, object]:
    candidates_payload = _read_json(
        OUTPUT_DIR / "split_models_operational_conversion_candidates" / "operational_conversion_candidates_summary.json"
    )
    current_state_payload = _read_json(OUTPUT_DIR / "split_models_operational_conversion_current_state.json")
    status_payload = _read_json(
        OUTPUT_DIR / "split_models_operational_conversion_status_snapshot" / "status_snapshot_summary.json"
    )
    promotion_payload = _read_json(
        OUTPUT_DIR
        / "split_models_operational_conversion_promotion_recommendation"
        / "promotion_recommendation_summary.json"
    )

    metric_lookup = _load_metric_lookup()
    interval_variant_names: set[str] = set()
    for summary_path in OUTPUT_DIR.glob("split_models_operational_conversion_*/*summary.json"):
        interval_variant_names.update(_collect_variant_strings(_read_json(summary_path)))

    excluded_variants = {
        candidates_payload["baseline_variant"],
        candidates_payload["aggressive_strongest_variant"],
    }
    new_interval_variants = sorted(name for name in interval_variant_names if name and name not in excluded_variants)

    selected_variants = [
        candidates_payload["aggressive_strongest_variant"],
        candidates_payload["baseline_variant"],
        current_state_payload["anchor_variant"],
        current_state_payload["best_quality_variant"],
        current_state_payload["recommended_representative_variant"],
        promotion_payload["growth_variant"],
        promotion_payload["drawdown_variant"],
    ]

    seen: set[str] = set()
    top_models: list[dict[str, object]] = []
    for variant in selected_variants:
        if variant in seen:
            continue
        seen.add(variant)
        metrics = metric_lookup.get(variant)
        if metrics:
            top_models.append(metrics)

    top_models.sort(key=lambda row: (float(row.get("cagr") or 0.0), -float(row.get("mdd") or 0.0)), reverse=True)

    payload = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "repo": "momentum",
        "report_focus": "model_metrics",
        "new_models_this_interval": len(new_interval_variants),
        "interval_variant_sample": new_interval_variants[:20],
        "promotion_status": current_state_payload["promotion_status"],
        "gate_status": current_state_payload["gate_status"],
        "drawdown_improver_count": status_payload["drawdown_improver_count"],
        "quality_overlay_count": status_payload["quality_overlay_count"],
        "no_op_count": status_payload["no_op_count"],
        "top_models": top_models,
    }
    return payload


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Momentum Model Scoreboard",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- new_models_this_interval: `{payload['new_models_this_interval']}`",
        f"- promotion_status: `{payload['promotion_status']}`",
        f"- gate_status: `{payload['gate_status']}`",
        f"- drawdown_improver_count: `{payload['drawdown_improver_count']}`",
        f"- quality_overlay_count: `{payload['quality_overlay_count']}`",
        f"- no_op_count: `{payload['no_op_count']}`",
        "",
        "| role | variant | CAGR | MDD | Sharpe | cost75bps_delta_vs_strongest | turnover | negWF |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["top_models"]:
        lines.append(
            "| {role} | `{variant}` | {cagr:.2%} | {mdd:.2%} | {sharpe:.4f} | {cost_metric} | {turnover} | {neg_wf} |".format(
                role=row.get("role", "candidate"),
                variant=row["variant"],
                cagr=float(row.get("cagr") or 0.0),
                mdd=float(row.get("mdd") or 0.0),
                sharpe=float(row.get("sharpe") or 0.0),
                cost_metric=(
                    "none"
                    if row.get("cost_metric") in {None, ""}
                    else f"{float(row['cost_metric']):+.2%}"
                ),
                turnover=(
                    "none"
                    if row.get("annual_turnover") in {None, ""}
                    else f"{float(row['annual_turnover']):.2f}"
                ),
                neg_wf=(
                    "none"
                    if row.get("negative_walk_forward_windows") in {None, ""}
                    else row["negative_walk_forward_windows"]
                ),
            )
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    SCOREBOARD_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    markdown = render_markdown(payload)
    summary_path = SCOREBOARD_DIR / "model_scoreboard_summary.json"
    markdown_path = SCOREBOARD_DIR / "model_scoreboard.md"
    summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    markdown_path.write_text(markdown, encoding="utf-8")
    print(json.dumps({"summary_path": str(summary_path), "markdown_path": str(markdown_path), "payload": payload}, indent=2))


if __name__ == "__main__":
    main()
