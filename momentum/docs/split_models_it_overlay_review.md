# IT Overlay Weak-Period Review

## Scope

- baseline compared: `rule_breadth_risk_off`
- candidate compared: `rule_breadth_it_risk_off`
- review window: `2021-04-30` to `2023-08-31`

## Why this rule was tested

- recent shadow loss diagnostics showed multiple weak months with `Information Technology` dominance
- candidate rule adds an extra exposure cut only when IT weight is at least `55%`

## Result

- full backtest result improved from MDD `-28.92%` to `-26.36%`
- Sharpe improved from `1.3723` to `1.4054`
- CAGR fell from `32.63%` to `30.35%`

## Weak-period finding

- overlay-triggered months in weak period: `2`
- baseline loss months in weak period: `12`
- loss months improved: `1`
- average net-return delta in triggered months: `+1.12%p`

## Key month

- `2021-11-30 -> 2022-02-28`
- baseline net return: `-15.29%`
- candidate net return: `-12.25%`
- improvement: `+3.04%p`

## Trade-off month

- `2023-05-31 -> 2023-06-30`
- baseline net return: `+3.93%`
- candidate net return: `+3.12%`
- give-up: `-0.81%p`

## Verdict

- `rule_breadth_it_risk_off` is a valid promoted baseline candidate
- the rule does not change the latest current book, so current shadow operations stay stable
- the rule is best understood as a selective crash-control overlay, not a broad return enhancer
