# Split Models Aggressive Branch Review

## Scope

- branch family: sector-constrained aggressive research variants
- retired comparison branches: `rule_sector_cap2_breadth_risk_off`, `rule_sector_cap2_breadth_it_risk_off`, `rule_sector_cap2_breadth_it_us5_cap`, `rule_sector_cap2_breadth_it_us5_top2_risk_on`, `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on`, `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_risk_on`
- surviving branch: `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`

## Full-period comparison

- `rule_sector_cap2_breadth_it_us5_cap`
  - CAGR: `39.72%`
  - MDD: `-29.27%`
  - Sharpe: `1.5423`
  - Annual turnover: `14.57`
- `rule_sector_cap2_breadth_it_us5_risk_on`
  - CAGR: `42.80%`
  - MDD: `-29.27%`
  - Sharpe: `1.5776`
  - Annual turnover: `14.99`
- `rule_sector_cap2_breadth_it_us5_top2_risk_on`
  - CAGR: `47.05%`
  - MDD: `-29.27%`
  - Sharpe: `1.6165`
  - Annual turnover: `15.00`
- `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on`
  - CAGR: `49.65%`
  - MDD: `-29.27%`
  - Sharpe: `1.6612`
  - Annual turnover: `14.88`
- `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_risk_on`
  - CAGR: `51.27%`
  - MDD: `-29.27%`
  - Sharpe: `1.6691`
  - Annual turnover: `14.96`
- `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count4_floor35_risk_on`
  - CAGR: `53.91%`
  - MDD: `-29.27%`
  - Sharpe: `1.6829`
  - Annual turnover: `15.02`
- `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count5_floor40_risk_on`
  - CAGR: `55.85%`
  - MDD: `-29.27%`
  - Sharpe: `1.6855`
  - Annual turnover: `15.03`
- `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count5_pen55_floor35_risk_on`
  - CAGR: `57.10%`
  - MDD: `-29.27%`
  - Sharpe: `1.6875`
  - Annual turnover: `15.07`
- `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count5_pen50_floor30_risk_on`
  - CAGR: `58.35%`
  - MDD: `-29.27%`
  - Sharpe: `1.6888`
  - Annual turnover: `15.11`
- `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count7_pen40_floor20_risk_on`
  - CAGR: `60.85%`
  - MDD: `-29.27%`
  - Sharpe: `1.6896`
  - Annual turnover: `15.18`
- `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count7_pen40_floor20_bonus18_risk_on`
  - CAGR: `62.16%`
  - MDD: `-29.27%`
  - Sharpe: `1.6896`
  - Annual turnover: `15.30`
- `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count7_pen40_floor20_bonus18_pow05_risk_on`
  - CAGR: `62.69%`
  - MDD: `-29.27%`
  - Sharpe: `1.6898`
  - Annual turnover: `15.31`
- `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on`
  - CAGR: `63.16%`
  - MDD: `-29.27%`
  - Sharpe: `1.6892`
  - Annual turnover: `15.32`

## Ranked-tail sensitivity review

- tail-penalty floor sweep is monotonic rather than brittle
- `floor=0.50`
  - CAGR: `50.46%`
  - Sharpe: `1.6654`
  - Annual turnover: `14.92`
- `floor=0.45`
  - CAGR: `50.87%`
  - Sharpe: `1.6673`
  - Annual turnover: `14.94`
- `floor=0.40`
  - CAGR: `51.27%`
  - Sharpe: `1.6691`
  - Annual turnover: `14.96`
- interpretation: pushing more penalty onto the weakest tail names improves the branch smoothly instead of exposing an unstable local optimum

## Ranked-tail surface review

- local parameter-surface sweep around the ranked-tail branch still improved rather than collapsing
- tested axes:
  - `breadth_bottom_slice_count`: `3`, `4`
  - `breadth_bottom_slice_penalty`: `0.60`, `0.65`
  - `breadth_bottom_slice_penalty_floor`: `0.35`, `0.40`, `0.45`
- combos tested: `12`
- best surface point:
  - bottom slice count `4`
  - bottom slice penalty `0.60`
  - bottom slice floor `0.35`
  - CAGR `53.91%`
  - Sharpe `1.6829`
- near-best combos within `1.00%p` CAGR of the best: `4`
- CAGR range across the local surface: `3.43%p`
- Sharpe range across the local surface: `0.0175`
- interpretation: the ranked-tail family still looks like a usable plateau rather than a one-cell spike, and the best local point moves to a deeper tail cut rather than reverting toward the old strongest

## Ranked-tail count4/floor35 candidate review

- versus `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_risk_on`
  - full-period CAGR delta: `+2.64%p`
  - full-period Sharpe delta: `+0.0138`
  - walk-forward positive CAGR windows: `3`
  - walk-forward negative CAGR windows: `0`
  - average walk-forward CAGR delta: `+2.82%p`
  - average walk-forward Sharpe delta: `+0.0087`
  - `75 bps` cost CAGR delta: `+2.40%p`
  - `75 bps` cost Sharpe delta: `+0.0222`
  - regime deltas:
    - `SPY UP`: `+0.269%p`
    - `SPY DOWN`: `+0.066%p`
    - `KOSPI UP`: `+0.304%p`
    - `KOSPI DOWN`: `+0.097%p`
  - concentration:
    - positive months `13`
    - negative months `9`
    - top 1 positive month share `16.36%`
    - top 3 positive month share `37.60%`
    - top 1 positive symbol share `27.25%`
    - top 3 positive symbol share `73.65%`
    - top symbol `PLTR`
- interpretation: deepening the ranked-tail source to `count=4 / floor=0.35` improved full-period, walk-forward, cost, and regime behavior together, while concentration stayed in the same compact-winner range rather than blowing out materially

## Ranked-tail count4/floor35 residual-edge review

- removing the three biggest winner-driven contributors `PLTR`, `NVDA`, and `MU` now flips the residual edge slightly negative
- total average monthly delta vs `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_risk_on`: `+0.206%p`
- average monthly delta attributable to `PLTR/NVDA/MU`: `+0.220%p`
- average residual monthly delta after excluding them: `-0.014%p`
- residual positive months: `7`
- residual negative months: `15`
- interpretation: the deeper ranked-tail branch is still a real strongest promotion, but its extra gain over the prior ranked-tail strongest is more tightly tied to the familiar `PLTR/NVDA/MU` winner cluster than the previous promotion step was

## Ranked-tail count4/floor35 basket-decay review

- cumulative winner-basket exclusions show the new strongest still survives top-one and top-two exclusions, but it turns negative once the top three winners are removed
- excluding only the top symbol `PLTR` leaves average monthly residual delta of `+0.124%p`
- excluding the top two symbols `PLTR/NVDA` leaves `+0.050%p`
- excluding the top three symbols `PLTR/NVDA/MU` flips residual delta slightly negative at `-0.014%p`
- excluding the top four symbols `PLTR/NVDA/MU/LRCX` pushes residual delta to `-0.042%p`
- excluding the top five symbols `PLTR/NVDA/MU/LRCX/0000J0` lowers it further to `-0.055%p`
- residual month balance also degrades quickly:
  - top1 excluded: `12` positive vs `10` negative months
  - top2 excluded: `9` positive vs `13` negative months
  - top3 excluded: `7` positive vs `15` negative months
  - top4 excluded: `7` positive vs `15` negative months
  - top5 excluded: `7` positive vs `15` negative months
- interpretation: the new strongest still looks better on full-period and robustness axes, but the marginal improvement itself is more basket-dependent than the prior ranked-tail promotion; the count4/floor35 step improved source efficiency more than it broadened the edge

## Ranked-tail count5/floor40 candidate review

- versus `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count4_floor35_risk_on`
  - full-period CAGR delta: `+1.94%p`
  - full-period Sharpe delta: `+0.0026`
  - walk-forward positive CAGR windows: `3`
  - walk-forward negative CAGR windows: `0`
  - average walk-forward CAGR delta: `+1.75%p`
  - average walk-forward Sharpe delta: `-0.0043`
  - `75 bps` cost CAGR delta: `+1.79%p`
  - `75 bps` cost Sharpe delta: `+0.0101`
  - regime deltas:
    - `SPY UP`: `+0.200%p`
    - `SPY DOWN`: `+0.045%p`
    - `KOSPI UP`: `+0.226%p`
    - `KOSPI DOWN`: `+0.070%p`
  - concentration:
    - positive months `15`
    - negative months `8`
    - top 1 positive month share `26.13%`
    - top 3 positive month share `56.08%`
    - top 1 positive symbol share `27.38%`
    - top 3 positive symbol share `66.20%`
    - top symbol `NVDA`
  - residual-edge:
    - average monthly delta `+0.152%p`
    - `PLTR/NVDA/MU` excluded residual delta `+0.003%p`
    - residual positive months `11`
    - residual negative months `12`
  - basket-decay:
    - exclude `PLTR`: residual `+0.124%p`
    - exclude `PLTR/NVDA`: residual `+0.050%p`
    - exclude `PLTR/NVDA/MU`: residual `+0.003%p`
- interpretation: widening the ranked-tail source to `count=5 / floor=0.40` improves CAGR again, keeps cost and regime support, and materially softens basket fragility versus the count4/floor35 strongest, even though the walk-forward Sharpe advantage is not cleaner than the headline CAGR improvement

## Ranked-tail count5/pen55/floor35 candidate review

- versus `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count5_floor40_risk_on`
  - full-period CAGR delta: `+1.25%p`
  - full-period Sharpe delta: `+0.0020`
  - walk-forward positive CAGR windows: `3`
  - walk-forward negative CAGR windows: `0`
  - average walk-forward CAGR delta: `+1.28%p`
  - average walk-forward Sharpe delta: `+0.0013`
  - `75 bps` cost CAGR delta: `+1.13%p`
  - `75 bps` cost Sharpe delta: `+0.0062`
  - `SPY UP` average delta: `+0.128%p`
  - `SPY DOWN` average delta: `+0.030%p`
  - `KOSPI UP` average delta: `+0.149%p`
  - `KOSPI DOWN` average delta: `+0.040%p`
  - positive months: `14`
  - negative months: `9`
  - average monthly delta: `+0.097%p`
  - top 1 positive month share: `22.97%`
  - top 3 positive month share: `44.86%`
  - top 1 positive symbol share: `27.33%`

## Broader challenger frontier review

- recent broader-challenger work did not replace the current strongest, but it did map the nearby `stronger vs broader` trade-off more clearly
- `hybrid_top2_plus_third01`
  - CAGR: `62.84%`
  - MDD: `-29.23%`
  - Sharpe: `1.6914`
  - interpretation: best recent broader challenger; slightly better Sharpe and lower concentration than the strongest, but still weaker on CAGR, cost, and walk-forward promotion quality
- `top2_split_49_51`
  - CAGR: `62.84%`
  - MDD: `-29.25%`
  - Sharpe: `1.6888`
  - interpretation: weaker than the hybrid challenger and not a meaningful mainline replacement
- `alt_family_top3_flat_bonus18`
  - CAGR: `46.12%`
  - MDD: `-29.27%`
  - Sharpe: `1.6105`
  - interpretation: useful boundary check for a genuinely broader family, but much too weak to remain a live strongest candidate
- the trade-off frontier therefore stays the same:
  - current strongest is still the `stronger` point
  - `hybrid_top2_plus_third01` is the current best `broader-but-weaker` challenger
  - top 3 positive symbol share: `74.08%`
  - top symbol: `PLTR`
  - `PLTR/NVDA/MU` excluded residual delta: `+0.006%p`
  - residual months: `10` positive / `9` negative
- interpretation: softening the tail penalty to `0.55` while keeping a deeper floor at `0.35` improves full-period, walk-forward, and cost together without worsening drawdown, and it keeps a small positive residual edge after removing `PLTR/NVDA/MU`

## Ranked-tail count5/pen50/floor30 candidate review

- versus `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count5_pen55_floor35_risk_on`
  - full-period CAGR delta: `+1.25%p`
  - full-period Sharpe delta: `+0.0013`
  - walk-forward positive CAGR windows: `3`
  - walk-forward negative CAGR windows: `0`
  - average walk-forward CAGR delta: `+1.29%p`
  - average walk-forward Sharpe delta: `+0.0010`
  - `75 bps` cost CAGR delta: `+1.13%p`
  - `75 bps` cost Sharpe delta: `+0.0054`
  - `SPY UP` average delta: `+0.128%p`
  - `SPY DOWN` average delta: `+0.030%p`
  - `KOSPI UP` average delta: `+0.149%p`
  - `KOSPI DOWN` average delta: `+0.040%p`
  - positive months: `14`
  - negative months: `9`
  - average monthly delta: `+0.097%p`
  - top 1 positive month share: `22.97%`
  - top 3 positive month share: `44.86%`
  - top 1 positive symbol share: `27.33%`
  - top 3 positive symbol share: `74.08%`
  - top symbol: `PLTR`
  - `PLTR/NVDA/MU` excluded residual delta: `+0.006%p`
  - residual months: `10` positive / `9` negative
- interpretation: widening the source relief one step further to `penalty=0.50 / floor=0.30` improves headline CAGR, walk-forward, and cost again without worsening drawdown, but fragility does not really improve versus the prior strongest; this is a stronger branch, not a broader one

## Ranked-tail walk-forward review

- 24-month / 12-month-step walk-forward windows compared: `4`
- `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_risk_on` beat `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on` on CAGR in `3` windows and lost in `0`
- average walk-forward CAGR delta vs `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on`: `+1.61%p`
- average walk-forward Sharpe delta: `+0.0050`
- latest window `2023-08-31 -> 2026-01-30` still improved CAGR by `+3.52%p`, though Sharpe slipped `-0.0119`
- interpretation: the ranked-tail branch is not a single-period artifact, but the latest window still shows the usual trade-off between stronger CAGR and slightly noisier return quality

## Ranked-tail cost sensitivity review

- even at `75 bps` one-way cost, `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_risk_on` remains ahead of `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on`
- `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_risk_on`
  - CAGR at `75 bps`: `39.71%`
  - Sharpe at `75 bps`: `1.3758`
- `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on`
  - CAGR at `75 bps`: `38.26%`
  - Sharpe at `75 bps`: `1.3626`
- interpretation: the new edge survives harsher execution assumptions and is not just a low-friction backtest artifact

## Ranked-tail start-date shift review

- shifting the backtest start date forward in `6`-month steps still leaves the ranked-tail branch ahead on CAGR every time
- start shifts tested: `5`
- positive CAGR shifts: `5`
- negative CAGR shifts: `0`
- positive Sharpe shifts: `4`
- negative Sharpe shifts: `1`
- average start-shift CAGR delta vs `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on`: `+2.21%p`
- average start-shift Sharpe delta: `+0.0074`
- tested start dates:
  - `2020-01-31`: CAGR delta `+1.62%p`, Sharpe delta `+0.0079`
  - `2020-08-31`: CAGR delta `+1.81%p`, Sharpe delta `+0.0071`
  - `2021-04-30`: CAGR delta `+2.05%p`, Sharpe delta `+0.0089`
  - `2021-11-30`: CAGR delta `+2.43%p`, Sharpe delta `+0.0140`
  - `2022-07-29`: CAGR delta `+3.15%p`, Sharpe delta `-0.0007`
- interpretation: the ranked-tail promotion is not tied to a single early sample start; the edge survives later-entry tests and generally strengthens as the sample moves forward, though the latest truncated window shows a tiny Sharpe giveback

## Ranked-tail concentration review

- versus `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on`:
  - positive months: `15`
  - negative months: `5`
  - average monthly delta: `+0.128%p`
  - top 1 positive month share: `23.06%`
  - top 3 positive month share: `45.13%`
  - top 1 positive symbol share: `27.14%`
  - top 3 positive symbol share: `73.35%`
  - top symbol driving the edge: `PLTR`
- interpretation: the new branch still draws on a compact winner basket, but it is not a single-month artifact and its incremental symbol concentration is not obviously worse than the prior convex branch

## Ranked-tail residual-edge review

- removing the three biggest winner-driven contributors `PLTR`, `NVDA`, and `MU` leaves a small but still positive residual edge
- total average monthly delta vs `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on`: `+0.128%p`
- average monthly delta attributable to `PLTR/NVDA/MU`: `+0.110%p`
- average residual monthly delta after excluding them: `+0.018%p`
- residual positive months: `9`
- residual negative months: `11`
- interpretation: the ranked-tail branch is still meaningfully tied to the familiar US winner basket, but unlike the prior convex branch it does not flip residual edge negative after removing the top three names

## Ranked-tail basket-decay review

- cumulative winner-basket exclusions still show dependence on a compact winner basket, but the decay is slower than the prior convex branch
- excluding only the top symbol `PLTR` leaves average monthly residual delta of `+0.087%p`
- excluding the top two symbols `PLTR/NVDA` leaves `+0.050%p`
- excluding the top three symbols `PLTR/NVDA/MU` leaves `+0.018%p`
- excluding the top four symbols `PLTR/NVDA/MU/LRCX` still leaves a barely positive `+0.004%p`
- excluding the top five symbols `PLTR/NVDA/MU/LRCX/0000J0` finally flips residual delta slightly negative at `-0.003%p`
- residual month balance also degrades more gradually:
  - top1 excluded: `13` positive vs `7` negative months
  - top2 excluded: `10` positive vs `10` negative months
  - top3 excluded: `9` positive vs `11` negative months
  - top4 excluded: `8` positive vs `12` negative months
  - top5 excluded: `8` positive vs `12` negative months
- interpretation: the new branch still depends on a compact winner basket, but the edge is less fragile than the prior convex strongest branch because it survives top-three and even top-four exclusions without turning materially negative

## Ranked-tail regime review

- the ranked-tail branch keeps a positive average delta in every regime bucket versus `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on`
- `SPY UP` average monthly delta: `+0.166%p`
- `SPY DOWN` average monthly delta: `+0.042%p`
- `KOSPI UP` average monthly delta: `+0.203%p`
- `KOSPI DOWN` average monthly delta: `+0.045%p`
- interpretation: this remains a pro-cyclical branch, but its edge does not disappear in down buckets

## Delta review

- months compared: `61`
- positive months for `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on` vs `rule_sector_cap2_breadth_it_us5_top2_risk_on`: `14`
- negative months: `9`
- average monthly net-return delta: `+0.191%p`
- best delta month: `2024-11-29 -> 2024-12-31`, `+3.31%p`
- worst delta month: `2023-05-31 -> 2023-06-30`, `-1.32%p`

## Weak-period review

- weak window: `2021-04-30 -> 2023-08-31`
- months compared: `25`
- baseline loss months: `11`
- loss months improved: `1`
- average monthly net-return delta: `+0.142%p`
- average loss-month delta: `+0.100%p`

## Prior top-slice concentration review

- months compared: `61`
- positive months: `16`
- negative months: `7`
- top 1 positive month share of total positive delta: `24.83%`
- top 3 positive month share: `46.06%`
- top 1 positive symbol share: `27.51%`
- top 3 positive symbol share: `74.91%`
- top symbols driving the edge: `PLTR`, `NVDA`, `MU`

## Concentration interpretation

- the month-level edge is not a single-month artifact, but it is still moderately concentrated in a handful of favorable months
- the symbol-level edge is much more concentrated than the month-level edge: most of the incremental alpha came from a small cluster of US information-technology winners
- that concentration is acceptable for an aggressive research branch, but it is a clear reason not to treat this as an operational baseline candidate

## Prior top-slice cost sensitivity review

- even at `75 bps` one-way cost, `rule_sector_cap2_breadth_it_us5_top2_risk_on` remains the best aggressive branch in this family
- `rule_sector_cap2_breadth_it_us5_top2_risk_on`
  - CAGR at `75 bps`: `35.76%`
  - Sharpe at `75 bps`: `1.3117`
- `rule_sector_cap2_breadth_it_us5_risk_on`
  - CAGR at `75 bps`: `31.82%`
  - Sharpe at `75 bps`: `1.2554`
- `rule_breadth_it_us5_cap`
  - CAGR at `75 bps`: `23.95%`
  - Sharpe at `75 bps`: `1.1090`
- cost drag is real, but the ranking survives; this reduces the chance that the top2 branch is only a low-friction backtest artifact

## Convex top-slice cost sensitivity review

- even at `75 bps` one-way cost, `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on` remains the strongest aggressive branch in this family
- `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on`
  - CAGR at `75 bps`: `38.26%`
  - Sharpe at `75 bps`: `1.3626`
- `rule_sector_cap2_breadth_it_us5_top2_risk_on`
  - CAGR at `75 bps`: `35.76%`
  - Sharpe at `75 bps`: `1.3117`
- `rule_sector_cap2_breadth_it_us5_risk_on`
  - CAGR at `75 bps`: `31.82%`
  - Sharpe at `75 bps`: `1.2554`
- cost drag still exists, but the convex branch keeps its ranking edge even under harsher execution assumptions

## Convex top-slice walk-forward review

- 24-month / 12-month-step walk-forward windows compared: `4`
- `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on` beat `rule_sector_cap2_breadth_it_us5_top2_risk_on` on CAGR in `3` windows and lost in `0`
- average walk-forward CAGR delta vs `rule_sector_cap2_breadth_it_us5_top2_risk_on`: `+2.22%p`
- average walk-forward Sharpe delta: `+0.0458`
- strongest relative window: `2023-08-31 -> 2026-01-30`, CAGR delta `+4.60%p`
- even the weak window `2021-04-30 -> 2023-08-31` still showed a positive CAGR delta of `+1.09%p`
- interpretation: the convex branch does not rely on a single recent burst; its edge survives across rolling windows and is still present in the weaker regime slice

## Convex top-slice regime review

- the convex branch is still pro-cyclical, but its average edge does not disappear in down-market buckets
- versus `rule_sector_cap2_breadth_it_us5_top2_risk_on`:
  - `SPY UP` average monthly delta: `+0.177%p`
  - `SPY DOWN` average monthly delta: `+0.223%p`
  - `KOSPI UP` average monthly delta: `+0.336%p`
  - `KOSPI DOWN` average monthly delta: `+0.032%p`
- joint regime view:
  - `SPY UP / KOSPI UP`: `+0.277%p`
  - `SPY DOWN / KOSPI DOWN`: `+0.083%p`
  - `SPY DOWN / KOSPI UP`: `+0.747%p`
  - `SPY UP / KOSPI DOWN`: `-0.023%p`
- interpretation: the edge is strongest in broadly favorable tapes, but it is not just an up-market artifact; only the `SPY UP / KOSPI DOWN` mixed bucket is mildly negative on average

## Prior top-slice walk-forward review

- 24-month / 12-month-step walk-forward windows compared: `4`
- `rule_sector_cap2_breadth_it_us5_top2_risk_on` beat `rule_sector_cap2_breadth_it_us5_risk_on` on CAGR in `3` windows and lost in `0`
- average walk-forward CAGR delta vs `rule_sector_cap2_breadth_it_us5_risk_on`: `+4.20%p`
- average walk-forward Sharpe delta: `+0.0250`
- strongest relative window: `2023-08-31 -> 2026-01-30`, CAGR delta `+10.37%p`
- even the weak window `2021-04-30 -> 2023-08-31` still showed a positive CAGR delta of `+1.22%p`

## Prior top-slice regime review

- the top2 branch performs best in favorable regimes, but it still keeps a positive average delta in adverse regimes
- versus `rule_sector_cap2_breadth_it_us5_risk_on`:
  - `SPY UP` average monthly delta: `+0.454%p`
  - `SPY DOWN` average monthly delta: `+0.082%p`
  - `KOSPI UP` average monthly delta: `+0.518%p`
  - `KOSPI DOWN` average monthly delta: `+0.139%p`
- interpretation: the branch is pro-cyclical, but not purely regime-fragile; its edge compresses in weak markets rather than fully flipping negative on average

## Prior top-slice residual-edge review

- removing the three biggest winner-driven contributors `PLTR`, `NVDA`, and `MU` leaves only a small residual edge
- total average monthly delta vs `rule_sector_cap2_breadth_it_us5_risk_on`: `+0.338%p`
- average monthly delta attributable to `PLTR/NVDA/MU`: `+0.322%p`
- average residual monthly delta after excluding them: `+0.016%p`
- residual positive months: `12`
- residual negative months: `11`
- leave-one-out checks are less alarming: excluding any one of `PLTR`, `NVDA`, or `MU` still leaves a meaningful residual edge of roughly `+0.220%p` to `+0.241%p` with `15` positive vs `8` negative months
- interpretation: the branch still has a small residual edge beyond the top winners, but the practical alpha is overwhelmingly tied to a narrow US tech winner cluster

## Prior top-slice basket-decay review

- cumulative winner-basket exclusions show the edge decays fast once the top US tech cluster is stripped out
- excluding only the top symbol `PLTR` still leaves average monthly residual delta of `+0.220%p`
- excluding the top two symbols `PLTR/NVDA` leaves `+0.113%p`
- excluding the top three symbols `PLTR/NVDA/MU` leaves only `+0.016%p`
- excluding the top four symbols `PLTR/NVDA/MU/LRCX` flips the residual edge slightly negative at `-0.028%p`
- residual month balance also collapses with basket size:
  - top1 excluded: `15` positive vs `8` negative months
  - top2 excluded: `13` positive vs `10` negative months
  - top3 excluded: `12` positive vs `11` negative months
  - top4 excluded: `11` positive vs `12` negative months
- interpretation: the branch is not a single-name illusion, but it is meaningfully dependent on a compact winner basket rather than a broad-based residual edge

## Convex top-slice concentration review

- versus `rule_sector_cap2_breadth_it_us5_top2_risk_on`, the new convex branch still avoids the single-shock-month failure mode but remains meaningfully concentrated
- months compared: `61`
- positive months: `14`
- negative months: `9`
- top 1 positive month share of total positive delta: `19.86%`
- top 3 positive month share: `54.96%`
- top 1 positive symbol share: `29.66%`
- top 3 positive symbol share: `68.17%`
- top symbols driving the edge: `NVDA`, `PLTR`, `MU`
- interpretation: month concentration is acceptable, but the incremental alpha still comes disproportionately from a narrow US winner cluster

## Convex top-slice basket-decay review

- cumulative winner-basket exclusions show the convex branch depends even more heavily on the top two winners than the prior strongest branch
- excluding only the top symbol `NVDA` still leaves average monthly residual delta of `+0.081%p`
- excluding the top two symbols `NVDA/PLTR` flips the residual edge slightly negative at `-0.015%p`
- excluding the top three symbols `NVDA/PLTR/MU` pushes residual delta further negative to `-0.062%p`
- residual month balance also degrades quickly:
  - top1 excluded: `11` positive vs `12` negative months
  - top2 excluded: `11` positive vs `12` negative months
  - top3 excluded: `9` positive vs `14` negative months
- interpretation: the new branch is stronger on headline performance, but it is also more explicitly dependent on a compact top-winner basket than the prior strongest branch

## Convex top-slice residual-edge review

- removing the three biggest winner-driven contributors `NVDA`, `PLTR`, and `MU` flips the residual edge negative
- total average monthly delta vs `rule_sector_cap2_breadth_it_us5_top2_risk_on`: `+0.191%p`
- average monthly delta attributable to `NVDA/PLTR/MU`: `+0.254%p`
- average residual monthly delta after excluding them: `-0.062%p`
- residual positive months: `9`
- residual negative months: `14`
- leave-one-out checks are still less alarming than the basket exclusion:
  - excluding `NVDA` leaves `+0.081%p`
  - excluding `PLTR` leaves `+0.095%p`
  - excluding `MU` leaves `+0.144%p`
- interpretation: the convex branch is not a single-name illusion, but its incremental alpha is overwhelmingly tied to a narrow `NVDA/PLTR/MU` winner cluster

## Interpretation

- the new convex top-slice overlay is a genuine structural improvement over the prior strongest branch: CAGR and Sharpe both improved again while MDD stayed flat and turnover fell slightly
- month-level improvement is still broad enough to stay out of the narrow-period reject bucket: `14` positive months versus `9` negative months with average monthly delta `+0.191%p`
- weak-period quality also improved slightly instead of getting worse: average weak-period delta stayed positive and loss-month average delta turned positive
- the cost-sensitivity check is supportive: even under `75 bps` one-way cost, the convex branch still leads both `top2_risk_on` and plain `risk_on`
- the walk-forward check is also supportive: convex stayed ahead of `top2_risk_on` in every non-tied rolling window and even kept a positive edge in the weak 2021-2023 slice
- the regime check is supportive: convex retains a positive average edge in both `SPY UP` and `SPY DOWN` buckets, with only one mixed joint-regime slice slightly negative
- the main remaining caution is stronger concentration: basket-decay and residual-edge checks both show that much of the incremental gain is even more dependent on the `NVDA/PLTR/MU` winner cluster than the prior strongest branch
- this remains a high-CAGR research branch, not an operational baseline candidate
- the new ranked-tail branch improves the convex source logic without changing the winner-harvesting target itself: it takes more weight from the weakest tail names, keeps the same top-two winners, and improves both CAGR and Sharpe while leaving MDD flat
- sensitivity, walk-forward, cost, and regime checks are all supportive enough to treat it as a genuine improvement over the prior convex branch, even though concentration remains a live caution
- residual-edge and basket-decay checks are supportive enough to treat this as a real robustness improvement rather than just a more aggressive way to harvest the same top basket: the edge still concentrates in `PLTR/NVDA/MU`, but it no longer turns negative immediately after removing them
- the next ranked-tail step, `count=4 / floor=0.35`, improves the same source logic one level further: it deepens the tail cut without changing the winner target, and it cleared the same promotion gates on full-period, walk-forward, cost, regime, and concentration
- the new strongest does come with one sharper caution: residual-edge and basket-decay rechecks show that the **incremental** gain from the `count=4 / floor=0.35` step is more tightly tied to `PLTR/NVDA/MU` than the previous ranked-tail promotion was, so this should still be framed as a stronger but not broader mixed-universe aggressive branch
- the `count=5 / floor=0.40` step improves that trade-off: it still concentrates in the same winner basket, but the incremental gain no longer turns residual edge clearly negative after removing `PLTR/NVDA/MU`, which makes it a stronger compromise between source efficiency and fragility than `count4 / floor35`
- the `count=5 / penalty=0.55 / floor=0.35` step improves the same source logic one level further: it keeps the broader tail source, relaxes the top-end tail cut slightly, improves CAGR and Sharpe again, and preserves a small positive residual edge after excluding `PLTR/NVDA/MU`
- the `count=5 / penalty=0.50 / floor=0.30` step improves headline strength one level further again: it relaxes the source cut slightly more, improves CAGR / Sharpe / walk-forward / cost together, but does not materially reduce winner-basket fragility relative to `count5 / pen55 / floor35`
- the `count=7 / penalty=0.40 / floor=0.20` step pushes the same source logic one level deeper again: it broadens the ranked-tail source materially, improves headline CAGR and benchmark-relative robustness again, and keeps residual edge positive without changing the mixed-universe interpretation
- the `count=6 / penalty=0.35 / floor=0.20 / bonus=0.18 / power=0.50` plateau local best cleared full-period, walk-forward, and cost head-to-head against the prior curved strongest, while keeping residual edge after excluding `PLTR/NVDA/MU` slightly positive rather than negative

## Verdict

- retire `rule_sector_cap2_breadth_risk_off`, `rule_sector_cap2_breadth_it_risk_off`, `rule_sector_cap2_breadth_it_us5_cap`, and `rule_sector_cap2_breadth_it_us5_top2_risk_on` from active aggressive research focus
- retire `rule_sector_cap2_breadth_it_us5_top2_convex_risk_on` from active aggressive research focus
- retire `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_risk_on` from active aggressive research focus
- retire `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count4_floor35_risk_on` from active aggressive research focus
- retire `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count5_floor40_risk_on` from active aggressive research focus
- retire `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count5_pen55_floor35_risk_on` from active aggressive research focus
- retire `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count5_pen50_floor30_risk_on` from active aggressive research focus
- retire `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count7_pen40_floor20_risk_on` from active aggressive research focus
- retire `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count7_pen40_floor20_bonus18_risk_on` from active aggressive research focus
- retire `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count7_pen40_floor20_bonus18_pow05_risk_on` from active aggressive research focus
- keep `rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on` as the single aggressive strong branch
- current best interpretation:
  - stronger than the prior `bonus18_pow05` strongest on full-period, walk-forward, and cost CAGR
  - still best understood as a mixed-universe aggressive construction rule rather than a broad stock-only model
- keep operational baseline separate as `rule_breadth_it_us5_cap`
