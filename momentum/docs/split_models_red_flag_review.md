# Split Models Red-Flag Review

## Scope

- target model: `rule_breadth_it_us5_cap`
- purpose: check whether the current `30%+` CAGR is strong evidence or a likely overstatement

## 1. Sample length is still short

- current backtest length is `61` months
- window: `2020-01-31` to `2026-02-27`
- verdict: this is enough to take seriously, but not enough to call the model fully verified

## 2. Weak-period resilience is only moderate

- weakest reviewed window: `2021-04-30` to `2023-08-31`
- weak-period CAGR: `8.80%`
- weak-period MDD: `-25.24%`
- weak-period Sharpe: `0.5038`
- verdict: the model survives, but it is not robust in all regimes

## 3. Sector concentration is real

- top sector contribution share: `51.44%`
- top 3 sector contribution share: `81.43%`
- biggest sector: `US Information Technology`
- verdict: a large part of total edge came from one sector family

## 4. Market dependence is high

- US contribution share: `86.73%`
- KR contribution share: `13.27%`
- verdict: this is not yet a balanced US/KR engine; it is mostly a US-driven strategy

## 5. A few names matter a lot

- top symbol contribution share: `18.41%`
- top 3 symbol contribution share: `41.54%`
- biggest single winner: `NVDA`
- verdict: the result is diversified enough to be interesting, but still depends meaningfully on a handful of names

## Overall judgment

- the model is not too fake to use
- the model is also not verified enough to trust blindly
- best description:
  - strong research result
  - reasonable small-capital live candidate
  - still vulnerable to regime dependence and concentration risk

## Decision

- keep small-capital live use limited to `rule_breadth_it_us5_cap`
- do not treat the current CAGR as a stable long-run expectation
- use this review as the default skeptical reference before increasing capital
