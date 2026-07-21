from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


SVG_WIDTH = 960
SVG_HEIGHT = 540


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _svg_document(inner: str, title: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{SVG_HEIGHT}" viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}">'
        '<rect width="100%" height="100%" fill="#f7f8fb"/>'
        f'<text x="40" y="45" font-family="Segoe UI, Arial, sans-serif" font-size="28" font-weight="700" fill="#18233a">{title}</text>'
        f"{inner}</svg>"
    )


def _bar_chart_svg(
    rows: list[dict[str, Any]],
    label_key: str,
    value_key: str,
    title: str,
    x_axis: str,
) -> str:
    chart_left = 80
    chart_top = 90
    chart_width = 820
    chart_height = 380
    max_value = max((_safe_float(row.get(value_key, 0.0)) for row in rows), default=1.0) or 1.0
    bar_gap = 16
    bar_width = max(24, int((chart_width - bar_gap * max(0, len(rows) - 1)) / max(1, len(rows))))

    parts = [
        f'<line x1="{chart_left}" y1="{chart_top + chart_height}" x2="{chart_left + chart_width}" y2="{chart_top + chart_height}" stroke="#4a587c" stroke-width="2"/>',
        f'<line x1="{chart_left}" y1="{chart_top}" x2="{chart_left}" y2="{chart_top + chart_height}" stroke="#4a587c" stroke-width="2"/>',
        f'<text x="{chart_left + chart_width / 2}" y="{chart_top + chart_height + 48}" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="16" fill="#33415c">{x_axis}</text>',
    ]

    for idx, row in enumerate(rows):
        value = _safe_float(row.get(value_key, 0.0))
        label = str(row.get(label_key, ""))
        bar_height = 0 if max_value == 0 else (value / max_value) * (chart_height - 10)
        x = chart_left + idx * (bar_width + bar_gap)
        y = chart_top + chart_height - bar_height
        parts.append(f'<rect x="{x}" y="{y}" width="{bar_width}" height="{bar_height}" fill="#3761d8" rx="4"/>')
        parts.append(
            f'<text x="{x + bar_width / 2}" y="{y - 8}" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="12" fill="#24314f">{value:.3f}</text>'
        )
        parts.append(
            f'<text x="{x + bar_width / 2}" y="{chart_top + chart_height + 20}" text-anchor="end" transform="rotate(-35 {x + bar_width / 2},{chart_top + chart_height + 20})" font-family="Segoe UI, Arial, sans-serif" font-size="12" fill="#33415c">{label}</text>'
        )

    return _svg_document("".join(parts), title)


def _scatter_svg(
    rows: list[dict[str, Any]],
    x_key: str,
    y_key: str,
    title: str,
    x_axis: str,
    y_axis: str,
    color_key: str,
) -> str:
    chart_left = 100
    chart_top = 90
    chart_width = 760
    chart_height = 360
    palette = {
        "new": "#3761d8",
        "mutation": "#dc5f3f",
        "mean_reversion": "#3761d8",
        "momentum": "#d87b1f",
        "volatility_breakout": "#b54680",
        "trend_following": "#2a9d6f",
        "range_trading": "#7d5bd6",
    }
    x_values = [_safe_float(row.get(x_key, 0.0)) for row in rows]
    y_values = [_safe_float(row.get(y_key, 0.0)) for row in rows]
    min_x = min(x_values, default=0.0)
    max_x = max(x_values, default=1.0)
    min_y = min(y_values, default=0.0)
    max_y = max(y_values, default=1.0)
    if min_x == max_x:
        max_x = min_x + 1.0
    if min_y == max_y:
        max_y = min_y + 1.0

    parts = [
        f'<line x1="{chart_left}" y1="{chart_top + chart_height}" x2="{chart_left + chart_width}" y2="{chart_top + chart_height}" stroke="#4a587c" stroke-width="2"/>',
        f'<line x1="{chart_left}" y1="{chart_top}" x2="{chart_left}" y2="{chart_top + chart_height}" stroke="#4a587c" stroke-width="2"/>',
        f'<text x="{chart_left + chart_width / 2}" y="{chart_top + chart_height + 48}" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="16" fill="#33415c">{x_axis}</text>',
        f'<text x="28" y="{chart_top + chart_height / 2}" text-anchor="middle" transform="rotate(-90 28,{chart_top + chart_height / 2})" font-family="Segoe UI, Arial, sans-serif" font-size="16" fill="#33415c">{y_axis}</text>',
    ]

    for row in rows:
        x_value = _safe_float(row.get(x_key, 0.0))
        y_value = _safe_float(row.get(y_key, 0.0))
        label = str(row.get("strategy_name", ""))
        color_value = str(row.get(color_key, ""))
        x = chart_left + ((x_value - min_x) / (max_x - min_x)) * chart_width
        y = chart_top + chart_height - ((y_value - min_y) / (max_y - min_y)) * chart_height
        fill = palette.get(color_value, "#3761d8")
        parts.append(f'<circle cx="{x}" cy="{y}" r="5" fill="{fill}" opacity="0.8"/>')
        parts.append(
            f'<title>{label} | {x_key}={x_value:.4f} | {y_key}={y_value:.4f}</title>'
        )

    return _svg_document("".join(parts), title)


def _funnel_svg(rows: list[dict[str, Any]], title: str) -> str:
    chart_left = 120
    chart_top = 110
    max_width = 700
    step_height = 70
    max_count = max((_safe_int(row.get("count", 0)) for row in rows), default=1) or 1
    parts: list[str] = []

    for idx, row in enumerate(rows):
        stage = str(row.get("stage", ""))
        count = _safe_int(row.get("count", 0))
        width = max(120, int((count / max_count) * max_width))
        x = chart_left + (max_width - width) / 2
        y = chart_top + idx * (step_height + 12)
        color = ["#1f4dbd", "#3761d8", "#5a7fe1", "#8ea7ee", "#c0cff7"][min(idx, 4)]
        parts.append(f'<rect x="{x}" y="{y}" width="{width}" height="{step_height}" fill="{color}" rx="10"/>')
        parts.append(f'<text x="{SVG_WIDTH / 2}" y="{y + 28}" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="18" font-weight="700" fill="#ffffff">{stage}</text>')
        parts.append(f'<text x="{SVG_WIDTH / 2}" y="{y + 50}" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="16" fill="#ffffff">{count}</text>')
    return _svg_document("".join(parts), title)


def _mermaid_system_overview() -> str:
    return """```mermaid
flowchart LR
    A[ResearchAgent] --> B[Engineer]
    B --> C[CandidateEvaluator]
    C --> D[DecisionPolicy]
    D --> E[Publish]
    E --> F[strategy_registry.json]
    C --> G[artifacts/{run_id}/candidates]
    D --> H[run_leaderboard.json]
    D --> I[decision_record.json]
    D --> J[approved_strategy.json]
```"""


def _mermaid_lineage(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "```mermaid\nflowchart LR\n    A[No lineage edges exported]\n```"
    lines = ["```mermaid", "flowchart LR"]
    for idx, row in enumerate(rows):
        parent = str(row.get("parent_strategy", "")).replace("-", "_")
        child = str(row.get("strategy_id", "")).replace("-", "_")
        lines.append(f"    P{idx}[{parent}] --> C{idx}[{child}]")
    lines.append("```")
    return "\n".join(lines)


def build_paper_figures(paper_results_dir: Path, output_dir: Path) -> dict[str, Path]:
    candidate_rows = _read_csv(paper_results_dir / "candidate_metrics.csv")
    rejection_rows = _read_csv(paper_results_dir / "rejection_reasons.csv")
    source_type_rows = _read_csv(paper_results_dir / "source_type_stats.csv")
    category_rows = _read_csv(paper_results_dir / "category_stats.csv")
    terminal_rows = _read_csv(paper_results_dir / "terminal_state_stats.csv")
    funnel_rows = _read_csv(paper_results_dir / "candidate_funnel.csv")
    lineage_rows = _read_csv(paper_results_dir / "lineage_edges.csv")

    outputs = {
        "system_overview": output_dir / "figure_1_system_overview.md",
        "candidate_funnel": output_dir / "figure_2_candidate_funnel.svg",
        "rejection_reasons": output_dir / "figure_3_rejection_reasons.svg",
        "source_type_comparison": output_dir / "figure_4_source_type_comparison.svg",
        "cross_asset_stability": output_dir / "figure_5_cross_asset_stability.svg",
        "regime_stability": output_dir / "figure_6_regime_stability.svg",
        "category_outcomes": output_dir / "figure_7_category_outcomes.svg",
        "terminal_states": output_dir / "figure_8_terminal_states.svg",
        "lineage_graph": output_dir / "figure_9_lineage_graph.md",
        "manifest": output_dir / "figure_manifest.json",
    }

    _write_text(outputs["system_overview"], _mermaid_system_overview())
    _write_text(outputs["candidate_funnel"], _funnel_svg(funnel_rows, "Figure 2. Candidate Funnel"))
    _write_text(outputs["rejection_reasons"], _bar_chart_svg(rejection_rows[:8], "failed_gate", "candidate_count", "Figure 3. Rejection Reasons", "failed gate"))
    _write_text(outputs["source_type_comparison"], _bar_chart_svg(source_type_rows, "source_type", "pass_rate", "Figure 4. New vs Mutation Pass Rate", "source type"))
    _write_text(outputs["cross_asset_stability"], _scatter_svg(candidate_rows, "sharpe_mean", "sharpe_std", "Figure 5. Cross-Asset Stability", "sharpe_mean", "sharpe_std", "source_type"))
    _write_text(outputs["regime_stability"], _scatter_svg(candidate_rows, "sharpe_mean", "sharpe_regime_std", "Figure 6. Regime Stability", "sharpe_mean", "sharpe_regime_std", "category"))
    _write_text(outputs["category_outcomes"], _bar_chart_svg(category_rows, "category", "pass_rate", "Figure 7. Category Pass Rate", "category"))
    _write_text(outputs["terminal_states"], _bar_chart_svg(terminal_rows, "decision", "run_count", "Figure 8. Run Terminal States", "decision"))
    _write_text(outputs["lineage_graph"], _mermaid_lineage(lineage_rows))
    _write_json(
        outputs["manifest"],
        {
            "paper_results_dir": str(paper_results_dir),
            "output_dir": str(output_dir),
            "figures": {name: str(path) for name, path in outputs.items()},
        },
    )
    return outputs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build figure-ready assets from paper_results exports.")
    parser.add_argument("--paper-results-dir", type=Path, default=Path("paper_results"))
    parser.add_argument("--output-dir", type=Path, default=Path("paper_figures"))
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    outputs = build_paper_figures(args.paper_results_dir, args.output_dir)
    for name, path in outputs.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
