import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


import pandas as pd


RISK_TICKERS = ["SPY", "QQQ", "IWM", "EFA", "EEM", "VNQ", "GLD", "PDBC", "HYG"]
DEFENSIVE_TICKERS = ["IEF", "TLT", "BIL"]


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def validate_batch1(snapshot: pd.DataFrame, score_df: pd.DataFrame, eligibility_df: pd.DataFrame) -> list[str]:
    issues: list[str] = []
    if snapshot.empty:
        issues.append("missing universe snapshot")
    if score_df.empty:
        issues.append("missing momentum score table")
    if eligibility_df.empty:
        issues.append("missing eligibility table")
    if issues:
        return issues

    snapshot_tickers = set(snapshot["Ticker"].astype(str))
    if snapshot.get("BatchStatus", pd.Series(dtype=object)).astype(str).ne("GO").any():
        issues.append("batch1 status is not GO")
    missing_snapshot = sorted((set(RISK_TICKERS) | set(DEFENSIVE_TICKERS)) - snapshot_tickers)
    if missing_snapshot:
        issues.append(f"batch1 snapshot missing tickers: {','.join(missing_snapshot)}")

    score_tickers = set(score_df["Ticker"].astype(str))
    missing_scores = sorted(set(RISK_TICKERS) - score_tickers)
    if missing_scores:
        issues.append(f"momentum table missing tickers: {','.join(missing_scores)}")

    elig_tickers = set(eligibility_df["Ticker"].astype(str))
    missing_elig = sorted(set(RISK_TICKERS) - elig_tickers)
    if missing_elig:
        issues.append(f"eligibility table missing tickers: {','.join(missing_elig)}")

    if "Status" in score_df.columns and score_df["Status"].astype(str).ne("OK").any():
        issues.append("momentum score table contains non-OK rows")
    if "Status" in eligibility_df.columns and eligibility_df["Status"].astype(str).ne("OK").any():
        issues.append("eligibility table contains non-OK rows")
    return issues


def choose_full_defense(snapshot: pd.DataFrame, signal_date: str) -> tuple[str, str]:
    defensive = snapshot[snapshot["Ticker"].astype(str).isin(["IEF", "TLT", "BIL"])].copy()
    if defensive.empty:
        return "BIL", "fallback_to_BIL_missing_defensive_data"
    row_map = {str(r["Ticker"]): r for _, r in defensive.iterrows()}
    try:
        ief_r3 = float(row_map["IEF"]["R3M"])
        tlt_r3 = float(row_map["TLT"]["R3M"])
    except Exception:
        return "BIL", "fallback_to_BIL_invalid_defensive_momentum"
    if ief_r3 <= 0 and tlt_r3 <= 0:
        return "BIL", "full_defense_both_non_positive_3M"
    if ief_r3 >= tlt_r3:
        return "IEF", "full_defense_higher_3M"
    return "TLT", "full_defense_higher_3M"


def build_portfolio(snapshot: pd.DataFrame, score_df: pd.DataFrame, eligibility_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    signal_date = str(score_df["SignalDate"].iloc[0])
    score_map = score_df.set_index("Ticker")
    merged = eligibility_df.copy()
    merged["Ticker"] = merged["Ticker"].astype(str)
    merged = merged.merge(
        score_df[["Ticker", "CompositeScore", "R3M", "R12M"]],
        on="Ticker",
        how="left",
    )
    eligible = merged[merged["Eligible"].fillna(0).astype(int) == 1].copy()
    eligible = eligible.sort_values(["CompositeScore", "Ticker"], ascending=[False, True]).reset_index(drop=True)
    selected = eligible.head(3).copy()
    selected_count = len(selected)

    defensive_weight = 1.0 - selected_count * (1.0 / 3.0)
    rows = []
    for _, row in selected.iterrows():
        rows.append(
            {
                "SignalDate": signal_date,
                "Ticker": str(row["Ticker"]),
                "Sleeve": "risk",
                "TargetWeight": 1.0 / 3.0,
                "SelectionReason": "top_eligible_risk",
            }
        )

    if selected_count == 0:
        defensive_ticker, defensive_reason = choose_full_defense(snapshot, signal_date)
        rows.append(
            {
                "SignalDate": signal_date,
                "Ticker": defensive_ticker,
                "Sleeve": "defensive",
                "TargetWeight": 1.0,
                "SelectionReason": defensive_reason,
            }
        )
        mode = "FULL_DEFENSE"
    elif defensive_weight > 0:
        rows.append(
            {
                "SignalDate": signal_date,
                "Ticker": "IEF",
                "Sleeve": "defensive",
                "TargetWeight": defensive_weight,
                "SelectionReason": "partial_defense_IEF_only",
            }
        )
        mode = "PARTIAL_DEFENSE"
    else:
        mode = "FULL_RISK"

    target = pd.DataFrame(rows).sort_values(["Sleeve", "Ticker"], ascending=[True, True]).reset_index(drop=True)
    target["TargetWeight"] = target["TargetWeight"].astype(float)

    defensive_decision = pd.DataFrame(
        [
            {
                "SignalDate": signal_date,
                "Mode": mode,
                "EligibleRiskCount": int(selected_count),
                "SelectedRiskTickers": ",".join(selected["Ticker"].astype(str).tolist()),
                "DefensiveTicker": "" if mode == "FULL_RISK" else str(target[target["Sleeve"] == "defensive"]["Ticker"].iloc[0]),
                "DefensiveWeight": 0.0 if mode == "FULL_RISK" else float(target[target["Sleeve"] == "defensive"]["TargetWeight"].iloc[0]),
                "RuleApplied": (
                    "none"
                    if mode == "FULL_RISK"
                    else "partial_defense_IEF_only"
                    if mode == "PARTIAL_DEFENSE"
                    else str(target[target["Sleeve"] == "defensive"]["SelectionReason"].iloc[0])
                ),
            }
        ]
    )

    decision_summary = pd.DataFrame(
        [
            {
                "Decision": "GO",
                "SignalDate": signal_date,
                "Mode": mode,
                "EligibleRiskCount": int(selected_count),
                "HoldingCount": int(len(target)),
                "WeightSum": float(target["TargetWeight"].sum()),
                "BlockingReason": "",
            }
        ]
    )
    return defensive_decision, target, decision_summary


def validate_portfolio(defensive_decision: pd.DataFrame, target: pd.DataFrame, decision_summary: pd.DataFrame) -> list[str]:
    issues: list[str] = []
    if target.empty:
        issues.append("empty target portfolio")
        return issues
    weight_sum = float(target["TargetWeight"].sum())
    if abs(weight_sum - 1.0) > 1e-9:
        issues.append("final weights do not sum to 1")
    risk_count = int((target["Sleeve"].astype(str) == "risk").sum())
    mode = str(defensive_decision.iloc[0]["Mode"])
    if risk_count > 3:
        issues.append("more than 3 risk holdings")
    if mode == "PARTIAL_DEFENSE":
        defensive = target[target["Sleeve"].astype(str) == "defensive"]
        if len(defensive) != 1 or str(defensive.iloc[0]["Ticker"]) != "IEF":
            issues.append("partial defense is not IEF only")
    if mode == "FULL_DEFENSE":
        defensive = target[target["Sleeve"].astype(str) == "defensive"]
        if len(defensive) != 1 or str(defensive.iloc[0]["Ticker"]) not in {"IEF", "TLT", "BIL"}:
            issues.append("full defense did not choose from IEF/TLT/BIL")
        if risk_count != 0:
            issues.append("full defense contains risk holdings")
    if mode == "FULL_RISK" and risk_count != 3:
        issues.append("full risk mode does not hold exactly 3 risk ETFs")
    if not decision_summary.empty and str(decision_summary.iloc[0]["Decision"]) != "GO":
        issues.append("decision summary not GO")
    return issues


def build_stop_outputs(reason: str, signal_date: str | None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    safe_date = signal_date or ""
    defensive_decision = pd.DataFrame(
        [
            {
                "SignalDate": safe_date,
                "Mode": "STOP",
                "EligibleRiskCount": 0,
                "SelectedRiskTickers": "",
                "DefensiveTicker": "",
                "DefensiveWeight": 0.0,
                "RuleApplied": "",
            }
        ]
    )
    target = pd.DataFrame(columns=["SignalDate", "Ticker", "Sleeve", "TargetWeight", "SelectionReason"])
    decision_summary = pd.DataFrame(
        [
            {
                "Decision": "STOP",
                "SignalDate": safe_date,
                "Mode": "STOP",
                "EligibleRiskCount": 0,
                "HoldingCount": 0,
                "WeightSum": 0.0,
                "BlockingReason": reason,
            }
        ]
    )
    return defensive_decision, target, decision_summary


def write_outputs(
    output_dir: Path,
    defensive_decision: pd.DataFrame,
    target: pd.DataFrame,
    decision_summary: pd.DataFrame,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    defensive_decision.to_csv(output_dir / "defensive_sleeve_decision.csv", index=False, encoding="utf-8-sig")
    target.to_csv(output_dir / "target_portfolio.csv", index=False, encoding="utf-8-sig")
    decision_summary.to_csv(output_dir / "decision_summary.csv", index=False, encoding="utf-8-sig")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Batch 2 portfolio construction for US ETF dual momentum MVP v1.")
    p.add_argument("--batch1-dir", type=str, default="backtests/us_etf_dual_momentum_mvp_v1_batch1")
    p.add_argument("--output-dir", type=str, default="backtests/us_etf_dual_momentum_mvp_v1_batch2")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    batch1_dir = Path(args.batch1_dir)
    output_dir = Path(args.output_dir)

    snapshot = load_csv(batch1_dir / "universe_snapshot.csv")
    score_df = load_csv(batch1_dir / "momentum_score_table.csv")
    eligibility_df = load_csv(batch1_dir / "eligibility_table.csv")

    issues = validate_batch1(snapshot, score_df, eligibility_df)
    signal_date = str(score_df["SignalDate"].iloc[0]) if not score_df.empty and "SignalDate" in score_df.columns else None

    if issues:
        defensive_decision, target, decision_summary = build_stop_outputs("; ".join(issues), signal_date)
    else:
        defensive_decision, target, decision_summary = build_portfolio(snapshot, score_df, eligibility_df)
        portfolio_issues = validate_portfolio(defensive_decision, target, decision_summary)
        if portfolio_issues:
            defensive_decision, target, decision_summary = build_stop_outputs("; ".join(portfolio_issues), signal_date)

    write_outputs(output_dir, defensive_decision, target, decision_summary)
    print(decision_summary.to_string(index=False))
    print()
    print(defensive_decision.to_string(index=False))
    if not target.empty:
        print()
        print(target.to_string(index=False))


if __name__ == "__main__":
    main()
