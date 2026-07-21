from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
FRONTIER_CSV = ROOT / "output" / "split_models_tradeoff_frontier_review" / "tradeoff_frontier_compare.csv"
AUDIT_JSON = ROOT / "output" / "split_models_trade_data_audit" / "trade_data_audit_summary.json"
BASELINE_SUMMARY_JSON = ROOT / "output" / "split_models_backtest" / "split_models_backtest_summary.json"
PROMOTION_SUMMARY_JSON = ROOT / "output" / "split_models_promotion_ledger" / "promotion_ledger_summary.json"
EXTERNAL_BENCHMARK_DIR = ROOT / "output" / "split_models_external_benchmark_review"
OUT_DIR = ROOT / "output" / "readme_assets"
BASELINE_VARIANT = "rule_breadth_it_us5_cap"
STRONGEST_VARIANT = "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on"
BASELINE_COLOR = "#2a7f62"
STRONGEST_COLOR = "#16324f"


def _fmt_pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _svg_text(x: float, y: float, text: str, size: int = 14, weight: str = "400", fill: str = "#16324f", anchor: str = "start") -> str:
    safe = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return (
        f'<text x="{x}" y="{y}" font-family="Segoe UI, Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{safe}</text>'
    )


def _load_frontier_rows() -> list[dict[str, str]]:
    with FRONTIER_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _load_audit_summary() -> dict:
    with AUDIT_JSON.open("r", encoding="utf-8") as f:
        return json.load(f)


def _load_baseline_summary() -> dict:
    with BASELINE_SUMMARY_JSON.open("r", encoding="utf-8") as f:
        return json.load(f)


def _load_promotion_summary() -> dict:
    with PROMOTION_SUMMARY_JSON.open("r", encoding="utf-8") as f:
        return json.load(f)


def _variant_short_name(variant: str) -> str:
    alias = {
        "rule_breadth_it_us5_cap": "baseline",
        "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count7_pen40_floor20_bonus18_pow05_risk_on": "retired",
        "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on": "strongest",
        "hybrid_top2_plus_third00125": "broader",
        "bonus_recipient_top1_third_85_15": "quality",
        "tail_skip_entry_flowweakest_new_bottom4_top25_mid75": "headline",
        "regime_weight_defensive_if_top2flowsoft": "defensive",
        "multi_step_confirm_top1_flowtop2": "fragile",
        "tail_release_top50_mid50": "redistribution",
    }
    return alias.get(variant, variant[:28])


def _write_svg(path: Path, width: int, height: int, parts: Iterable[str]) -> None:
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{path.stem}">',
        '<rect width="100%" height="100%" fill="#f7f4ec"/>',
        *parts,
        "</svg>",
    ]
    path.write_text("\n".join(svg), encoding="utf-8")


def _frontier_lookup() -> dict[str, dict[str, str]]:
    return {row["Variant"]: row for row in _load_frontier_rows()}


def _load_nav_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _compute_drawdown_series(nav_points: list[float]) -> list[float]:
    running_peak = nav_points[0]
    drawdowns: list[float] = []
    for nav in nav_points:
        running_peak = max(running_peak, nav)
        drawdowns.append(nav / running_peak - 1.0)
    return drawdowns


def _load_baseline_vs_strongest_context() -> dict[str, object]:
    baseline_summary = _load_baseline_summary()["trading_book"]
    frontier = _frontier_lookup()
    strongest_summary = frontier[STRONGEST_VARIANT]
    baseline_rows = _load_nav_rows(EXTERNAL_BENCHMARK_DIR / f"{BASELINE_VARIANT}_nav.csv")
    strongest_rows = _load_nav_rows(EXTERNAL_BENCHMARK_DIR / f"{STRONGEST_VARIANT}_nav.csv")

    if len(baseline_rows) != len(strongest_rows):
        raise ValueError("Baseline and strongest NAV series length mismatch")

    labels = ["2020-01"] + [row["NextDate"][:7] for row in baseline_rows]
    baseline_nav = [1.0] + [float(row["NAV"]) for row in baseline_rows]
    strongest_nav = [1.0] + [float(row["NAV"]) for row in strongest_rows]
    return {
        "baseline_summary": baseline_summary,
        "strongest_summary": strongest_summary,
        "labels": labels,
        "baseline_nav": baseline_nav,
        "strongest_nav": strongest_nav,
    }


def _append_time_axis_grid(
    parts: list[str],
    labels: list[str],
    left: int,
    top: int,
    plot_w: int,
    plot_h: int,
) -> None:
    def sx(idx: int) -> float:
        return left + idx / (len(labels) - 1) * plot_w

    x_tick_indices = [0, 12, 24, 36, 48, len(labels) - 1]
    seen: set[int] = set()
    for idx in x_tick_indices:
        if idx in seen or idx >= len(labels):
            continue
        seen.add(idx)
        x = sx(idx)
        parts.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top + plot_h}" stroke="#ece6db"/>')
        parts.append(_svg_text(x, top + plot_h + 28, labels[idx], 12, "400", "#5c6b73", "middle"))


def build_frontier_svg() -> Path:
    rows = _load_frontier_rows()
    selected = []
    wanted = {
        "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on",
        "hybrid_top2_plus_third00125",
        "bonus_recipient_top1_third_85_15",
        "tail_skip_entry_flowweakest_new_bottom4_top25_mid75",
        "regime_weight_defensive_if_top2flowsoft",
        "multi_step_confirm_top1_flowtop2",
        "tail_release_top50_mid50",
    }
    for row in rows:
        if row["Variant"] in wanted:
            selected.append(
                {
                    "name": _variant_short_name(row["Variant"]),
                    "cagr": float(row["CAGR"]),
                    "mdd": abs(float(row["MDD"])),
                    "sharpe": float(row["Sharpe"]),
                }
            )

    width = 980
    height = 640
    left = 90
    right = 80
    top = 90
    bottom = 90
    plot_w = width - left - right
    plot_h = height - top - bottom
    min_x = min(p["mdd"] for p in selected) - 0.005
    max_x = max(p["mdd"] for p in selected) + 0.005
    min_y = min(p["cagr"] for p in selected) - 0.01
    max_y = max(p["cagr"] for p in selected) + 0.01
    max_s = max(p["sharpe"] for p in selected)
    min_s = min(p["sharpe"] for p in selected)

    def sx(v: float) -> float:
        return left + (v - min_x) / (max_x - min_x) * plot_w

    def sy(v: float) -> float:
        return top + plot_h - (v - min_y) / (max_y - min_y) * plot_h

    def sr(v: float) -> float:
        return 10 + (v - min_s) / (max_s - min_s + 1e-9) * 16

    palette = {
        "strongest": "#16324f",
        "broader": "#7c9d96",
        "quality": "#2a7f62",
        "headline": "#c56b2d",
        "defensive": "#596a7b",
        "fragile": "#b8405e",
        "redistribution": "#8d5a97",
    }

    parts: list[str] = [
        _svg_text(50, 44, "Current Truth Frontier", 28, "700"),
        _svg_text(50, 68, "x = drawdown severity (lower is better)   y = CAGR   bubble size = Sharpe", 14, "400", "#5c6b73"),
        f'<rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="#fffdfa" stroke="#d7d0c4"/>',
    ]

    for i in range(6):
        x = left + plot_w * i / 5
        y = top + plot_h * i / 5
        parts.append(f'<line x1="{x}" y1="{top}" x2="{x}" y2="{top + plot_h}" stroke="#ece6db"/>')
        parts.append(f'<line x1="{left}" y1="{y}" x2="{left + plot_w}" y2="{y}" stroke="#ece6db"/>')
        x_val = min_x + (max_x - min_x) * i / 5
        y_val = max_y - (max_y - min_y) * i / 5
        parts.append(_svg_text(x, top + plot_h + 26, _fmt_pct(x_val), 12, "400", "#5c6b73", "middle"))
        parts.append(_svg_text(left - 12, y + 4, _fmt_pct(y_val), 12, "400", "#5c6b73", "end"))

    parts.append(_svg_text(left + plot_w / 2, height - 24, "Max Drawdown (absolute)", 14, "600", "#36454f", "middle"))
    parts.append(f'<g transform="translate(24 {top + plot_h / 2}) rotate(-90)">{_svg_text(0, 0, "CAGR", 14, "600", "#36454f", "middle")}</g>')

    for point in selected:
        x = sx(point["mdd"])
        y = sy(point["cagr"])
        r = sr(point["sharpe"])
        color = palette.get(point["name"], "#6b7280")
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{color}" fill-opacity="0.84" stroke="#ffffff" stroke-width="2"/>')
        parts.append(_svg_text(x, y - r - 8, point["name"], 13, "600", color, "middle"))
        parts.append(_svg_text(x, y + r + 18, f"{point['sharpe']:.3f} Sharpe", 11, "400", "#5c6b73", "middle"))

    out_path = OUT_DIR / "current_truth_frontier.svg"
    _write_svg(out_path, width, height, parts)
    return out_path


def build_holdings_svg() -> Path:
    audit = _load_audit_summary()
    strongest = next(model for model in audit["models"] if model["label"] == "strongest")
    holdings = strongest["holdings"][:7]
    width = 980
    height = 520
    left = 220
    top = 90
    bar_h = 36
    gap = 18
    max_bar_w = 660
    max_weight = max(item["target_weight"] for item in holdings)

    parts: list[str] = [
        _svg_text(50, 44, "Latest Strongest Holdings Snapshot", 28, "700"),
        _svg_text(50, 68, f"Signal date {strongest['latest_signal_date']}   entered {', '.join(strongest['entered_symbols'][:6])}", 14, "400", "#5c6b73"),
    ]

    for idx, item in enumerate(holdings):
        y = top + idx * (bar_h + gap)
        label = f"{item['market']}:{item['symbol']}"
        name = item.get("name") or item["symbol"]
        weight = item["target_weight"]
        bar_w = weight / max_weight * max_bar_w
        color = "#16324f" if idx < 2 else "#c56b2d"
        parts.append(_svg_text(50, y + 24, label, 15, "700", "#16324f"))
        parts.append(_svg_text(50, y + 42, name, 12, "400", "#5c6b73"))
        parts.append(f'<rect x="{left}" y="{y}" width="{max_bar_w}" height="{bar_h}" rx="8" fill="#ebe5da"/>')
        parts.append(f'<rect x="{left}" y="{y}" width="{bar_w:.1f}" height="{bar_h}" rx="8" fill="{color}"/>')
        parts.append(_svg_text(left + min(bar_w + 14, max_bar_w - 6), y + 24, _fmt_pct(weight), 14, "700", "#16324f"))

    parts.append(_svg_text(50, height - 28, "Top 2 KR ETF sleeve dominates the latest book, with US industrial / health care names filling the residual tail.", 14, "400", "#5c6b73"))

    out_path = OUT_DIR / "strongest_latest_holdings.svg"
    _write_svg(out_path, width, height, parts)
    return out_path


def build_equity_curve_svg() -> Path:
    context = _load_baseline_vs_strongest_context()
    baseline_summary = context["baseline_summary"]
    strongest_summary = context["strongest_summary"]
    labels = context["labels"]
    baseline_points = context["baseline_nav"]
    strongest_points = context["strongest_nav"]
    strongest_final_nav = strongest_points[-1]

    width = 1100
    height = 620
    left = 95
    right = 50
    top = 95
    bottom = 90
    plot_w = width - left - right
    plot_h = height - top - bottom
    max_nav = max(max(baseline_points), max(strongest_points)) * 1.06
    min_nav = min(min(baseline_points), min(strongest_points)) * 0.96

    def sx(idx: int) -> float:
        return left + idx / (len(labels) - 1) * plot_w

    def sy(nav: float) -> float:
        return top + plot_h - (nav - min_nav) / (max_nav - min_nav) * plot_h

    def series_path(values: list[float]) -> str:
        coords = [f"{sx(i):.1f},{sy(v):.1f}" for i, v in enumerate(values)]
        return "M " + " L ".join(coords)

    parts: list[str] = [
        _svg_text(50, 44, "Baseline vs Strongest Equity Curve", 28, "700"),
        _svg_text(50, 68, "Normalized NAV since 2020-01. This is the cleanest README view of robustness-first operating truth versus the current aggressive research leader.", 14, "400", "#5c6b73"),
        f'<rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="#fffdfa" stroke="#d7d0c4"/>',
    ]

    y_ticks = 6
    for i in range(y_ticks + 1):
        y = top + plot_h * i / y_ticks
        nav = max_nav - (max_nav - min_nav) * i / y_ticks
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}" stroke="#ece6db"/>')
        parts.append(_svg_text(left - 12, y + 4, f"{nav:.1f}x", 12, "400", "#5c6b73", "end"))

    _append_time_axis_grid(parts, labels, left, top, plot_w, plot_h)

    parts.append(f'<path d="{series_path(baseline_points)}" fill="none" stroke="{BASELINE_COLOR}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>')
    parts.append(f'<path d="{series_path(strongest_points)}" fill="none" stroke="{STRONGEST_COLOR}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>')

    for idx, values, color in [
        (len(baseline_points) - 1, baseline_points, BASELINE_COLOR),
        (len(strongest_points) - 1, strongest_points, STRONGEST_COLOR),
    ]:
        parts.append(f'<circle cx="{sx(idx):.1f}" cy="{sy(values[idx]):.1f}" r="5.5" fill="{color}" stroke="#fffdfa" stroke-width="2"/>')

    parts.append(f'<rect x="690" y="118" width="360" height="88" rx="16" fill="#f5eee1" stroke="#d8cab2"/>')
    parts.append(f'<circle cx="718" cy="144" r="6" fill="{BASELINE_COLOR}"/>')
    parts.append(_svg_text(734, 149, f"baseline  final NAV {baseline_summary['FinalNAV']:.2f}x   CAGR {_fmt_pct(baseline_summary['CAGR'])}", 13, "700"))
    parts.append(f'<circle cx="718" cy="178" r="6" fill="{STRONGEST_COLOR}"/>')
    parts.append(_svg_text(734, 183, f"strongest final NAV {strongest_final_nav:.2f}x   CAGR {_fmt_pct(float(strongest_summary['CAGR']))}", 13, "700"))

    parts.append(_svg_text(left + plot_w / 2, height - 28, "Normalized NAV", 14, "600", "#36454f", "middle"))
    parts.append(_svg_text(50, height - 28, "The strongest finishes far higher, but the baseline remains the calmer operating anchor with shallower drawdown.", 14, "400", "#5c6b73"))

    out_path = OUT_DIR / "baseline_vs_strongest_equity_curve.svg"
    _write_svg(out_path, width, height, parts)
    return out_path


def build_drawdown_curve_svg() -> Path:
    context = _load_baseline_vs_strongest_context()
    baseline_summary = context["baseline_summary"]
    strongest_summary = context["strongest_summary"]
    labels = context["labels"]
    baseline_drawdown = _compute_drawdown_series(context["baseline_nav"])
    strongest_drawdown = _compute_drawdown_series(context["strongest_nav"])

    width = 1100
    height = 620
    left = 95
    right = 50
    top = 95
    bottom = 90
    plot_w = width - left - right
    plot_h = height - top - bottom
    min_dd = min(min(baseline_drawdown), min(strongest_drawdown)) * 1.06
    max_dd = 0.0

    def sx(idx: int) -> float:
        return left + idx / (len(labels) - 1) * plot_w

    def sy(drawdown: float) -> float:
        return top + (drawdown - min_dd) / (max_dd - min_dd) * plot_h

    def series_path(values: list[float]) -> str:
        coords = [f"{sx(i):.1f},{sy(v):.1f}" for i, v in enumerate(values)]
        return "M " + " L ".join(coords)

    parts: list[str] = [
        _svg_text(50, 44, "Baseline vs Strongest Drawdown Curve", 28, "700"),
        _svg_text(50, 68, "Underwater view since 2020-01. This isolates the operating calmness advantage of the baseline against the higher-return but deeper-drawdown strongest branch.", 14, "400", "#5c6b73"),
        f'<rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="#fffdfa" stroke="#d7d0c4"/>',
    ]

    y_ticks = 5
    for i in range(y_ticks + 1):
        y = top + plot_h * i / y_ticks
        dd = max_dd - (max_dd - min_dd) * i / y_ticks
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}" stroke="#ece6db"/>')
        parts.append(_svg_text(left - 12, y + 4, _fmt_pct(dd), 12, "400", "#5c6b73", "end"))

    _append_time_axis_grid(parts, labels, left, top, plot_w, plot_h)

    zero_y = sy(0.0)
    parts.append(f'<line x1="{left}" y1="{zero_y:.1f}" x2="{left + plot_w}" y2="{zero_y:.1f}" stroke="#b8aea0" stroke-width="2"/>')

    parts.append(f'<path d="{series_path(baseline_drawdown)}" fill="none" stroke="{BASELINE_COLOR}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>')
    parts.append(f'<path d="{series_path(strongest_drawdown)}" fill="none" stroke="{STRONGEST_COLOR}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>')

    baseline_min_idx = min(range(len(baseline_drawdown)), key=lambda i: baseline_drawdown[i])
    strongest_min_idx = min(range(len(strongest_drawdown)), key=lambda i: strongest_drawdown[i])
    for idx, values, color in [
        (baseline_min_idx, baseline_drawdown, BASELINE_COLOR),
        (strongest_min_idx, strongest_drawdown, STRONGEST_COLOR),
    ]:
        parts.append(f'<circle cx="{sx(idx):.1f}" cy="{sy(values[idx]):.1f}" r="5.5" fill="{color}" stroke="#fffdfa" stroke-width="2"/>')

    parts.append(f'<rect x="690" y="118" width="360" height="88" rx="16" fill="#f5eee1" stroke="#d8cab2"/>')
    parts.append(f'<circle cx="718" cy="144" r="6" fill="{BASELINE_COLOR}"/>')
    parts.append(_svg_text(734, 149, f"baseline  worst drawdown {_fmt_pct(float(baseline_summary['MDD']))}", 13, "700"))
    parts.append(f'<circle cx="718" cy="178" r="6" fill="{STRONGEST_COLOR}"/>')
    parts.append(_svg_text(734, 183, f"strongest worst drawdown {_fmt_pct(float(strongest_summary['MDD']))}", 13, "700"))

    parts.append(_svg_text(left + plot_w / 2, height - 28, "Drawdown from prior peak", 14, "600", "#36454f", "middle"))
    parts.append(_svg_text(50, height - 28, "The baseline gives up less capital in peak-to-trough terms, which is why it still anchors the operating path despite the weaker terminal NAV.", 14, "400", "#5c6b73"))

    out_path = OUT_DIR / "baseline_vs_strongest_drawdown_curve.svg"
    _write_svg(out_path, width, height, parts)
    return out_path


def build_promotion_map_svg() -> Path:
    frontier = _frontier_lookup()
    baseline_summary = _load_baseline_summary()
    promotion_summary = _load_promotion_summary()
    strongest_variant = promotion_summary["candidate_variant"]
    retired_variant = promotion_summary["baseline_variant"]
    strongest_row = frontier[strongest_variant]

    baseline_metrics = baseline_summary["trading_book"]
    strongest_metrics = {
        "CAGR": float(strongest_row["CAGR"]),
        "MDD": abs(float(strongest_row["MDD"])),
        "Sharpe": float(strongest_row["Sharpe"]),
        "AnnualTurnover": float(strongest_row["AnnualTurnover"]),
    }

    width = 1180
    height = 860
    parts: list[str] = [
        _svg_text(50, 46, "Current Promotion Map", 28, "700"),
        _svg_text(50, 72, "Operational truth on the left, aggressive research leader on the right, and the current near-miss routes below.", 14, "400", "#5c6b73"),
    ]

    def card(x: int, y: int, w: int, h: int, fill: str = "#fffdfa", stroke: str = "#d7d0c4", rx: int = 20) -> None:
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')

    def pill(x: int, y: int, text: str, fill: str, text_fill: str = "#fffdfa", w: int = 126) -> None:
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="30" rx="15" fill="{fill}"/>')
        parts.append(_svg_text(x + w / 2, y + 20, text, 13, "700", text_fill, "middle"))

    def metric_row(x: int, y: int, label: str, value: str, label_fill: str = "#5c6b73", value_fill: str = "#16324f") -> None:
        parts.append(_svg_text(x, y, label, 13, "600", label_fill))
        parts.append(_svg_text(x + 180, y, value, 13, "700", value_fill))

    def draw_multiline(x: int, y: int, lines: list[str], size: int = 12, weight: str = "400", fill: str = "#5c6b73", line_gap: int = 16) -> None:
        for line_idx, line in enumerate(lines):
            parts.append(_svg_text(x, y + line_idx * line_gap, line, size, weight, fill))

    def wrap_text(text: str, max_chars: int = 32) -> list[str]:
        words = text.split()
        lines: list[str] = []
        current = ""
        for word in words:
            if len(word) > max_chars:
                if current:
                    lines.append(current)
                    current = ""
                for i in range(0, len(word), max_chars):
                    lines.append(word[i:i + max_chars])
                continue
            tentative = word if not current else f"{current} {word}"
            if len(tentative) <= max_chars:
                current = tentative
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    # Top story cards.
    card(50, 106, 320, 228, "#fdf8ef")
    pill(72, 126, "Operate Here", "#2a7f62")
    parts.append(_svg_text(72, 180, "Operational baseline", 23, "700"))
    parts.append(_svg_text(72, 208, "rule_breadth_it_us5_cap", 13, "600", "#7c5c2b"))
    metric_row(72, 246, "CAGR", _fmt_pct(baseline_metrics["CAGR"]))
    metric_row(72, 272, "MDD", f"-{_fmt_pct(abs(baseline_metrics['MDD']))}")
    metric_row(72, 298, "Sharpe", f"{baseline_metrics['Sharpe']:.4f}")
    metric_row(72, 324, "Turnover", f"{baseline_metrics['AnnualTurnover']:.2f}")

    card(430, 106, 700, 248, "#fffaf2")
    pill(454, 126, "Research Leader", "#16324f", w=150)
    parts.append(_svg_text(454, 180, "Aggressive strongest", 23, "700"))
    draw_multiline(454, 208, wrap_text(strongest_variant, 58), 13, "600", "#7c5c2b")
    metric_row(454, 268, "CAGR", _fmt_pct(strongest_metrics["CAGR"]))
    metric_row(454, 294, "MDD", f"-{_fmt_pct(strongest_metrics['MDD'])}")
    metric_row(454, 320, "Sharpe", f"{strongest_metrics['Sharpe']:.4f}")
    metric_row(454, 346, "Turnover", f"{strongest_metrics['AnnualTurnover']:.2f}")
    parts.append(_svg_text(730, 268, "vs retired strongest", 13, "600", "#5c6b73"))
    parts.append(_svg_text(730, 294, f"+{_fmt_pct(promotion_summary['full_period_cagr_delta'])} CAGR", 13, "700", "#2a7f62"))
    parts.append(_svg_text(730, 320, f"+{_fmt_pct(promotion_summary['cost_latest_cagr_delta'])} at 75 bps", 13, "700", "#2a7f62"))
    parts.append(_svg_text(730, 346, f"{promotion_summary['walkforward_positive_cagr_windows']} positive walk-forward windows", 13, "700", "#16324f"))

    card(820, 20, 310, 70, "#f5eee1", "#d8cab2", 16)
    parts.append(_svg_text(844, 48, "Latest promotion leg", 14, "700"))
    parts.append(_svg_text(844, 70, "retired strongest  ->  current strongest", 13, "600", "#5c6b73"))

    parts.append('<line x1="370" y1="220" x2="430" y2="220" stroke="#c56b2d" stroke-width="4" stroke-linecap="round"/>')
    parts.append('<polygon points="430,220 414,212 414,228" fill="#c56b2d"/>')
    parts.append(_svg_text(400, 204, "higher-conviction", 13, "700", "#c56b2d", "middle"))
    parts.append(_svg_text(400, 242, "research path", 12, "400", "#5c6b73", "middle"))

    parts.append(_svg_text(50, 392, "Near-Miss Routes Still Open", 22, "700"))
    parts.append(_svg_text(50, 418, "None of these clears promotion grade yet, but each explains where the frontier is still pressuring the leader.", 14, "400", "#5c6b73"))

    near_miss_cards = [
        ("Broader", "hybrid_top2_plus_third00125", "#7c9d96", "broader exposure", "weaker overall"),
        ("Quality", "bonus_recipient_top1_third_85_15", "#2a7f62", "best blended-quality extension", "still not promotion-grade"),
        ("Headline", "tail_skip_entry_flowweakest_new_bottom4_top25_mid75", "#c56b2d", "lower-turnover headline improvement", "quality still weaker"),
        ("Defensive weighting", "regime_weight_defensive_if_top2flowsoft", "#596a7b", "closest defensive weighting point", "cost and fragility still weaker"),
        ("Stronger but fragile", "multi_step_confirm_top1_flowtop2", "#b8405e", "stronger on headline and Sharpe", "concentration worsens too much"),
        ("Redistribution", "tail_release_top50_mid50", "#8d5a97", "strongest redistribution contender", "drawdown still too weak"),
    ]

    start_x = 50
    start_y = 452
    card_w = 340
    card_h = 150
    x_gap = 30
    y_gap = 24
    for idx, (axis, variant, color, matters, blocked) in enumerate(near_miss_cards):
        row = idx // 3
        col = idx % 3
        x = start_x + col * (card_w + x_gap)
        y = start_y + row * (card_h + y_gap)
        card(x, y, card_w, card_h)
        pill_width = 170 if axis in {"Defensive weighting", "Stronger but fragile"} else 132
        pill(x + 18, y + 18, axis, color, w=pill_width)
        draw_multiline(x + 18, y + 68, wrap_text(variant, 30), 12, "600", "#7c5c2b")
        lines = wrap_text(matters, 28)
        parts.append(_svg_text(x + 18, y + 102, "Why it matters", 12, "700", "#16324f"))
        draw_multiline(x + 18, y + 122, lines, 12, "400", "#5c6b73")

        block_lines = wrap_text(f"Blocked: {blocked}", 30)
        draw_multiline(x + 178, y + 102, block_lines, 12, "600", "#8b3d3d")

    parts.append(_svg_text(50, 804, "Read the repo as a promotion ledger: run the baseline, defend the strongest, and keep the near-miss routes visible until one truly clears the bar.", 14, "400", "#5c6b73"))

    out_path = OUT_DIR / "promotion_map.svg"
    _write_svg(out_path, width, height, parts)
    return out_path


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    build_frontier_svg()
    build_equity_curve_svg()
    build_drawdown_curve_svg()
    build_holdings_svg()
    build_promotion_map_svg()
    print(f"Wrote visuals to {OUT_DIR}")


if __name__ == "__main__":
    main()
