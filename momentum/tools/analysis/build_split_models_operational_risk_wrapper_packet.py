from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from split_models.backtest import BacktestConfig, _baseline_variant_map, _cost_sensitivity, _run_trading_backtest_variant, _summarize_returns, _walkforward_summary
from tools.analysis.analyze_split_models_tradeoff_frontier import _build_context


OUTPUT_DIR = REPO_ROOT / "output" / "split_models_operational_risk_wrapper"
BASELINE_VARIANT = "rule_breadth_it_us5_cap"
EXPOSURES = [1.00, 0.85, 0.80, 0.75, 0.70]
MDD_GATE = -0.20


def _pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.2f}%"


def _scaled_nav(nav: pd.DataFrame, exposure: float) -> pd.DataFrame:
    out = nav.copy()
    out["RawNetReturn"] = pd.to_numeric(out["NetReturn"], errors="coerce").fillna(0.0)
    out["NetReturn"] = out["RawNetReturn"] * exposure
    out["NAV"] = (1.0 + out["NetReturn"]).cumprod()
    if "Turnover" in out.columns:
        out["Turnover"] = pd.to_numeric(out["Turnover"], errors="coerce").fillna(0.0) * exposure
    out["Exposure"] = exposure
    out["CashWeight"] = 1.0 - exposure
    return out


def _drawdown_table(nav: pd.DataFrame, limit: int = 5) -> list[dict[str, object]]:
    df = nav.copy()
    df["SignalDate"] = pd.to_datetime(df["SignalDate"])
    df["NextDate"] = pd.to_datetime(df["NextDate"])
    df["NAV"] = pd.to_numeric(df["NAV"], errors="coerce").fillna(0.0)
    df["Peak"] = df["NAV"].cummax()
    df["Drawdown"] = df["NAV"] / df["Peak"] - 1.0
    rows: list[dict[str, object]] = []
    used: set[int] = set()
    for _ in range(limit):
        remaining = df.loc[~df.index.isin(used)]
        if remaining.empty:
            break
        trough_idx = int(remaining["Drawdown"].idxmin())
        trough = df.loc[trough_idx]
        if float(trough["Drawdown"]) >= 0:
            break
        before = df.loc[:trough_idx]
        peak_value = float(before["Peak"].max())
        peak = before[before["NAV"] == peak_value].iloc[-1]
        window = df[(df["SignalDate"] >= peak["SignalDate"]) & (df["NextDate"] <= trough["NextDate"])]
        rows.append(
            {
                "start": peak["NextDate"].strftime("%Y-%m-%d"),
                "trough": trough["NextDate"].strftime("%Y-%m-%d"),
                "depth": float(trough["Drawdown"]),
                "months": int(len(window)),
                "avg_exposure": float(window["Exposure"].mean()),
            }
        )
        used.update(int(idx) for idx in window.index)
    return rows


def _row_for(nav: pd.DataFrame, exposure: float) -> dict[str, object]:
    metrics = _summarize_returns(nav["NetReturn"], nav["NextDate"])
    turnover = float(pd.to_numeric(nav.get("Turnover", pd.Series(dtype=float)), errors="coerce").fillna(0.0).mean() * 12.0)
    walk = _walkforward_summary(nav, window_months=24, step_months=12)
    cost = _cost_sensitivity(nav, [20])
    cost20 = cost.iloc[0].to_dict() if not cost.empty else {}
    return {
        "model": BASELINE_VARIANT,
        "overlay": f"fixed_exposure_{int(round(exposure * 100)):03d}",
        "exposure": exposure,
        "cash_weight": 1.0 - exposure,
        "cagr": float(metrics["CAGR"]),
        "mdd": float(metrics["MDD"]),
        "sharpe": float(metrics["Sharpe"]),
        "calmar": float(metrics["CAGR"] / abs(metrics["MDD"])) if metrics["MDD"] else None,
        "annual_turnover": turnover,
        "cost20_cagr": float(cost20.get("CAGR")) if cost20 else None,
        "cost20_sharpe": float(cost20.get("Sharpe")) if cost20 else None,
        "negative_walk_forward_windows": int((pd.to_numeric(walk["CAGR"], errors="coerce") < 0).sum()) if not walk.empty else None,
        "oos_min_mdd": float(pd.to_numeric(walk["MDD"], errors="coerce").min()) if not walk.empty else None,
        "gate_result": "pass_mdd_margin" if float(metrics["MDD"]) >= MDD_GATE else "fail_mdd_margin",
        "top_drawdowns": _drawdown_table(nav),
    }


def _build_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Risk Wrapper Packet",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- frozen_model: `{payload['frozen_model']}`",
        f"- best_overlay: `{payload['best_overlay']}`",
        f"- verdict: {payload['verdict']}",
        "",
        "| overlay | exposure | cash | CAGR | MDD | Sharpe | Calmar | cost20 CAGR | neg WF | gate |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            "| `{}` | {:.0%} | {:.0%} | {} | {} | {:.4f} | {} | {} | {} | `{}` |".format(
                row["overlay"],
                float(row["exposure"]),
                float(row["cash_weight"]),
                _pct(float(row["cagr"])),
                _pct(float(row["mdd"])),
                float(row["sharpe"]),
                "n/a" if row["calmar"] is None else f"{float(row['calmar']):.4f}",
                _pct(row["cost20_cagr"]),
                row["negative_walk_forward_windows"],
                row["gate_result"],
            )
        )
    best = next(row for row in payload["rows"] if row["overlay"] == payload["best_overlay"])
    lines.extend(["", "## Worst Drawdowns For Best Overlay", "", "| rank | start | trough | depth | months |", "| ---: | --- | --- | ---: | ---: |"])
    for idx, row in enumerate(best["top_drawdowns"], start=1):
        lines.append(f"| {idx} | `{row['start']}` | `{row['trough']}` | {_pct(float(row['depth']))} | {row['months']} |")
    return "\n".join(lines).rstrip() + "\n"


def build_payload() -> dict[str, object]:
    cfg = BacktestConfig()
    universe, price_cache, flow_cache, monthly_close, signal_dates = _build_context(cfg)
    variant = _baseline_variant_map()[BASELINE_VARIANT]
    result = _run_trading_backtest_variant(universe, price_cache, flow_cache, monthly_close, signal_dates, cfg, variant)
    rows = [_row_for(_scaled_nav(result["nav"], exposure), exposure) for exposure in EXPOSURES]
    passing = [row for row in rows if row["gate_result"] == "pass_mdd_margin"]
    ranked = passing or rows
    best = sorted(ranked, key=lambda row: (row["gate_result"] != "pass_mdd_margin", -float(row["sharpe"]), -float(row["cagr"])))[0]
    if best["gate_result"] == "pass_mdd_margin":
        verdict = f"{best['overlay']} clears the fixed MDD gate with CAGR {_pct(float(best['cagr']))}, MDD {_pct(float(best['mdd']))}, Sharpe {float(best['sharpe']):.4f}."
    else:
        verdict = "No fixed exposure wrapper clears the MDD gate; escalate to volatility targeting or regime kill-switch."
    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "report_focus": "stock_operational_risk_wrapper",
        "frozen_model": BASELINE_VARIANT,
        "objective": "convert raw alpha into an operating review packet by risk-budgeting exposure, not by mutating alpha",
        "mdd_gate": MDD_GATE,
        "best_overlay": best["overlay"],
        "verdict": verdict,
        "rows": rows,
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    latest_json = OUTPUT_DIR / "risk_wrapper_packet_latest.json"
    latest_md = OUTPUT_DIR / "risk_wrapper_packet_latest.md"
    latest_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    latest_md.write_text(_build_markdown(payload), encoding="utf-8")
    print(json.dumps({"json": str(latest_json), "markdown": str(latest_md), "best_overlay": payload["best_overlay"]}, indent=2))


if __name__ == "__main__":
    main()
