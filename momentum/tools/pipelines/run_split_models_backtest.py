from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from split_models.backtest import BacktestConfig, run_backtests

BASELINE_VARIANT = "rule_breadth_it_us5_cap"


def main() -> None:
    outputs = run_backtests(config=BacktestConfig(baseline_variant=BASELINE_VARIANT))
    summary = outputs["trading_book_backtest_summary"].iloc[0]
    print(f"baseline_variant={BASELINE_VARIANT}")
    print(f"months={int(summary['Months'])}")
    print(f"cagr={summary['CAGR']:.4f}")
    print(f"mdd={summary['MDD']:.4f}")
    print(f"sharpe={summary['Sharpe']:.4f}")
    print(f"tenbagger_occurrences={len(outputs['tenbagger_backtest_occurrences'])}")


if __name__ == "__main__":
    main()
