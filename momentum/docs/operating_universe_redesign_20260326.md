# Operating Universe Redesign 2026-03-26

## Why the old 41-name universe is not acceptable
- It was a manually frozen operating set, not a rule-based investable universe.
- It mixed several low-liquidity and low-price names with otherwise tradable names.
- It is suitable for continuity checks, but not as a defensible long-term operating universe.

## Design principle
- Separate `research universe` from `operating universe`.
- Research universe can stay broad.
- Operating universe must be rule-based and investable.

## Institutional-style operating universe rule
Preset name:
- `institutional_v1`

Stock rules:
- `Bars >= 750`
- `LastClose >= 1000`
- `AvgDailyValue60D >= 5,000,000,000 KRW`
- `MedianDailyValue60D >= 2,000,000,000 KRW`
- `ZeroValueDays60D <= 1`

ETF rules:
- `Bars >= 180`
- `AvgDailyValue60D >= 500,000,000 KRW`
- `MedianDailyValue60D >= 100,000,000 KRW`
- `ZeroValueDays60D <= 1`

Implementation:
- [D:\AI\모멘텀 투자\kis_operating_universe.py](D:\AI\모멘텀 투자\kis_operating_universe.py)

## Current result
- Selected stocks: `38`
- Selected ETFs: `6`
- Total: `44`

Files:
- [D:\AI\모멘텀 투자\backtests\kis_operating_universe_candidates_institutional_v1.csv](D:\AI\모멘텀 투자\backtests\kis_operating_universe_candidates_institutional_v1.csv)
- [D:\AI\모멘텀 투자\backtests\kis_operating_universe_review_institutional_v1.csv](D:\AI\모멘텀 투자\backtests\kis_operating_universe_review_institutional_v1.csv)
- [D:\AI\모멘텀 투자\data\prices_operating_institutional_v1](D:\AI\모멘텀 투자\data\prices_operating_institutional_v1)

## Old 41-name universe review
Dropped from the old operating universe:
- `0000H0`
- `0000Y0`
- `000020`
- `000040`
- `000070`
- `000080`
- `012200`
- `043220`
- `059210`
- `065170`
- `066900`
- `067000`
- `074610`
- `090710`
- `189330`
- `348340`
- `356890`

## Recommendation
- Keep the old `prices_operating` only as a comparison baseline.
- Use `prices_operating_institutional_v1` as the next candidate operating universe for full rerun.
- Compare:
  - old frozen 41-name universe
  - new `institutional_v1` universe
- Only then decide whether to promote the new universe into canonical daily operation.
