# BTC 1d Restart Baseline

This note defines the default restart scope when the BTC 1d research lane is resumed from a cold start.

Next document:

- use [first_backtest_runbook.md](C:\AI\Crypto\docs\first_backtest_runbook.md) for the actual first-pass execution order after the scope is fixed.

## Default Data Window

- Primary research window: latest `6-8 years` of daily data.
- Minimum acceptable window for a serious decision: `5 years`.
- Do not treat `1-2 year` results as promotion evidence. That is only a local regime check.
- Do not anchor the main decision on very early crypto history if that pushes the window far past `8-10 years`; early market structure is too different from the current BTC/ETH regime.

## Default Validation Cuts

Within the main `6-8 year` window, always split the readout into:

- trend expansion / bull segments
- sharp drawdown / liquidation segments
- sideways or recovery segments

If a candidate only works in one of those conditions, it is not robust enough for default promotion.

## Asset Scope

Default research order:

1. `BTCUSDT` as the main design target
2. `ETHUSDT` as the required cross-check
3. `3-5` additional liquid majors only after BTC/ETH behavior is understood

Recommended initial cross-check basket:

- `BTCUSDT`
- `ETHUSDT`
- `SOLUSDT`
- `BNBUSDT`

Optional fifth name:

- a single additional liquid major such as `XRPUSDT`

## Scope Rules

- Do not restart from `BTC only` and then generalize to all crypto.
- Do not open a wide altcoin universe at the start; the first question is whether the mechanism survives on BTC and remains directionally coherent on ETH and a few liquid majors.
- Treat alt expansion as a robustness layer, not as the main optimization target.

## Promotion Standard

A candidate is only interesting when:

- it survives the main BTC window,
- it does not materially collapse on ETH,
- and it stays directionally coherent on the liquid-major cross-check basket.

If BTC is strong but ETH breaks the same mechanism cleanly, treat that as a structure warning, not as a minor nuisance.

## Practical Restart Recommendation

If the repo is resumed from scratch, start with:

1. BTC latest `8 years` daily backtest
2. ETH matched-window replay
3. one short report comparing whether the edge is `BTC-specific`, `BTC-led but portable`, or `non-portable`

Only after that should the lane expand to more majors or execution-plumbing follow-up.
