# Implementable 12-1 Momentum in U.S. Large-Cap Equities:
# Sector Caps, Liquidity Screens, Trading Frictions, and Capital Constraints

## Structured Abstract

### Purpose

This paper evaluates whether the canonical `12-1` cross-sectional momentum signal can remain economically useful after being translated into a realistically implementable long-only strategy in U.S. large-cap equities.

### Design/methodology/approach

The tested strategy selects the top 20 stocks by `12-1` momentum, equal-weights positions, and limits holdings to at most three names per sector. The implementation imposes a 60-day median dollar-volume filter, a minimum price rule, monthly rebalancing, explicit transaction-cost assumptions, and a capital-feasibility check based on whole-share execution. To reduce the most obvious survivorship problem in the earlier research build, the stock universe is reconstructed with a Wikipedia-revision-based point-in-time approximation of S&P 100 membership. The stock strategy is compared against an ETF risk-budget benchmark, a residual sector rotation benchmark, and a same-universe equal-weight benchmark. Factor spanning regressions are estimated with Newey-West robust standard errors.

### Findings

Under the current point-in-time approximation, the stock momentum strategy delivers `CAGR 14.85%`, `MDD -30.67%`, and `Sharpe 0.88`, compared with `CAGR 12.18%`, `MDD -35.80%`, and `Sharpe 0.75` for the same-universe equal-weight benchmark. The strategy remains positive in all five walk-forward test windows. Relative to the same-universe benchmark, the estimated break-even one-way transaction cost is about `42.8 bps` on a CAGR-match basis. Capacity diagnostics indicate approximate strategy capacity of about `2.2M USD` at a `0.1%` participation threshold and about `22.2M USD` at a `1.0%` participation threshold of 60-day median dollar volume.

### Research limitations/implications

The current point-in-time universe is still an approximation based on public-web revision history rather than an institutional constituent-history database with authoritative delisting-return treatment. Accordingly, the paper should be viewed as a strong submission-oriented draft rather than a final publication-ready estimate.

### Originality/value

The contribution of the paper is not anomaly discovery. Instead, it documents how a familiar momentum signal behaves once sector caps, liquidity filters, transaction costs, and capital constraints are imposed jointly. The paper is best read as an implementation-focused quantitative portfolio study.

## 1. Introduction

Momentum is one of the most persistent empirical regularities in asset pricing, yet the distance between academic momentum portfolios and real portfolios that an allocator can actually trade remains large. Standard academic constructions often abstract away from sector concentration, trading frictions, capital constraints, and implementability at the account level. In live settings, however, these frictions matter at least as much as the signal itself.

This paper examines whether a simple long-only `12-1` momentum strategy in U.S. large-cap equities remains attractive after those practical frictions are imposed explicitly. The strategy ranks eligible names by lagged price momentum, selects the top 20, equal-weights them, restricts holdings to at most three names per sector, and rebalances monthly. Eligibility is limited by a minimum price rule and a liquidity screen based on 60-day median dollar volume. This produces a portfolio design that is intentionally transparent and easy to audit.

The paper does not claim to discover a new factor. The correct question is narrower: once a canonical momentum signal is forced through a realistic portfolio-construction process, how much of the economic value remains? That is the central implementation question addressed here.

Three benchmark families are used. The first is an ETF risk-budget allocation strategy, which serves as a diversified lower-turnover baseline. The second is a residual sector rotation strategy in U.S. sector ETFs, which serves as a more aggressive timing-based comparator. The third, and most important, is a same-universe equal-weight benchmark built from the same approximate constituent history as the stock strategy. This final benchmark is critical because it prevents the momentum strategy from being compared only against more defensive ETF portfolios and instead asks whether momentum improves upon a broad equity allocation drawn from the same opportunity set.

The current evidence is encouraging but should be interpreted carefully. After replacing the earlier static current-member universe with a Wikipedia-revision-based point-in-time approximation, the stock momentum strategy still delivers higher raw return than all three benchmarks and remains positive in every walk-forward test window. However, once standard factor regressions are run with Newey-West robust standard errors, the strategy appears to be best understood as an implementable momentum exposure rather than a source of statistically strong independent alpha beyond known momentum risk.

That distinction is not a weakness if the paper is positioned correctly. The practical contribution lies in showing what remains of momentum after sector caps, liquidity filters, explicit trading costs, and account-size constraints are imposed together. The paper also quantifies break-even transaction costs and capacity limits, which allows the discussion to move beyond backtest return tables toward actual investability.

The remainder of the paper proceeds as follows. Section 2 reviews related literature. Section 3 describes the data and universe construction. Section 4 presents the strategy design and benchmarks. Section 5 reports the empirical results, including factor regressions, break-even cost analysis, and capacity diagnostics. Section 6 discusses the main limitations. Section 7 concludes.

## 2. Related Literature

This paper lies at the intersection of five literature streams.

First, it draws on the classic literature on cross-sectional momentum. Jegadeesh and Titman (1993) establish the central empirical result that recent winners tend to continue outperforming recent losers over intermediate horizons. The present paper does not attempt to revisit that question from scratch. Instead, it takes the standard `12-1` signal as given and studies how much of its economic usefulness survives once realistic implementation frictions are imposed.

Second, the paper relates directly to the literature on trading frictions and anomaly implementability. Lesmond, Schill, and Zhou (2004) raise the possibility that momentum profits are overstated once trading costs are considered. Korajczyk and Sadka (2004) show that both transaction costs and capacity matter, especially for concentrated or high-turnover designs. Novy-Marx and Velikov (2016) further emphasize that anomaly profitability should be evaluated net of realistic turnover-dependent costs. This literature motivates the paper's explicit cost stress, break-even cost analysis, and capacity diagnostics.

Third, the paper is related to the literature on sector and industry effects in momentum. Moskowitz and Grinblatt (1999) show that industry momentum explains an important share of stock momentum. This matters here because the tested strategy includes a hard sector-cap rule. The sector limit is therefore not an arbitrary heuristic; it is an attempt to reduce hidden macro-thematic concentration while preserving the stock-selection content of the signal.

Fourth, the paper connects to the literature on liquidity and liquidity risk. Amihud (2002) and Pastor and Stambaugh (2003) show that liquidity conditions are priced and that liquidity risk has cross-sectional significance. Because momentum strategies naturally rebalance into recent winners, they can become fragile when liquidity deteriorates. This justifies the use of a rolling dollar-volume filter and the discussion of limited capacity.

Fifth, the paper contributes to the smaller but practically important literature on implementability for capital-constrained investors. Equal-weight strategies in high-priced large-cap stocks may be theoretically simple but operationally infeasible in smaller accounts because target weights cannot be approximated with whole-share execution. By quantifying a minimum-capital threshold and participation-rate-based capacity ceilings, this paper extends the momentum discussion from factor performance to investor feasibility.

## 3. Data

### 3.1 Stock universe

The stock universe is intended to approximate the S&P 100 over time. The earlier research build used a static present-day membership file, which created a severe survivorship problem. The current draft replaces that setup with a point-in-time approximation constructed from historical Wikipedia revision snapshots of the S&P 100 page. This is a substantial improvement because historical additions and removals now enter the sample over time rather than being fixed from the end of the sample backward.

The resulting approximate constituent history contains `132` distinct symbols over the full sample. The stock backtest summary reports `StaticUniverseBiasFlag = 0` and `UniverseBiasNote = WIKIPEDIA_REVISION_POINT_IN_TIME_APPROX`, which is directionally correct but should still be treated as an intermediate research approximation rather than a final institutional-quality constituent-history solution.

### 3.2 ETF universe

The ETF benchmark universe contains `18` liquid instruments spanning broad equity, duration, credit, gold, REIT, and sector sleeves. This universe supports both a lower-turnover diversified allocation benchmark and a more concentrated sector-rotation benchmark.

### 3.3 Sample period

The point-in-time approximation stock strategy currently spans `2015-01-02` to `2026-03-27`. The ETF strategies span roughly the same period, subject to factor-data availability for the residual sector rotation benchmark.

### 3.4 Variables and execution assumptions

The stock strategy uses daily adjusted closing prices to compute the momentum signal and daily returns. Liquidity is proxied by the rolling 60-day median of dollar trading volume. The sector-rotation benchmark estimates residual alpha from rolling regressions of daily sector ETF excess returns on the Fama-French five factors. The current draft still assumes return realization from end-of-day series rather than an explicit next-open or VWAP execution model, so this remains a known limitation for final submission.

## 4. Strategy Design

### 4.1 Stock momentum strategy

The main stock strategy computes:

`Momentum12_1 = Price(t-21) / Price(t-252) - 1`

This excludes the most recent month and follows the standard momentum convention designed to reduce contamination from short-term reversal effects. At each month-end rebalance, the strategy ranks all eligible names by this signal, selects the top 20, applies a cap of three names per sector, and equal-weights the selected names.

Eligibility requires:

- positive `12-1` momentum
- price of at least `10 USD`
- 60-day median dollar volume of at least `100,000,000 USD`
- at least `252` available trading days
- active membership in the point-in-time approximation on the rebalance date

### 4.2 ETF risk-budget benchmark

The ETF risk-budget benchmark rebalances weekly, screens for ETF liquidity, and caps individual ETF weights at `35%`. At the end of the current sample, the portfolio is heavily allocated to `SHY` and high-grade bond proxies, which is consistent with its role as a lower-volatility benchmark rather than an equity-selection engine.

### 4.3 Residual sector rotation benchmark

The residual sector rotation strategy estimates annualized intercepts from rolling regressions of sector ETF excess returns on the daily Fama-French five factors. At each month-end rebalance, it holds the top three sector ETFs with positive residual alpha and allocates any unused weight to `SHY`.

### 4.4 Same-universe equal-weight benchmark

The same-universe benchmark is constructed from the same approximate constituent history as the stock strategy. On each month-end rebalance date, it equal-weights all active members with available price data and then holds them until the next rebalance. This benchmark is intentionally simple but important: it isolates whether momentum adds value relative to remaining broadly invested in the same large-cap opportunity set.

### 4.5 Transaction costs and capital feasibility

The current cost grid applies one-way transaction costs of `5`, `7`, `10`, `15`, and `25` basis points. The paper also computes the capital required to purchase at least one share of each target position and derives capacity diagnostics based on participation in rolling median dollar volume.

## 5. Results

### 5.1 Full-sample comparison

Table 1 summarizes the full-sample comparison.

| Strategy | CAGR | MDD | Sharpe |
| --- | ---: | ---: | ---: |
| US ETF RiskBudget | 4.82% | -14.05% | 0.81 |
| US Same-Universe EW Benchmark | 12.18% | -35.80% | 0.75 |
| US Residual Sector Rotation | 7.43% | -32.79% | 0.49 |
| US Stock Mom12_1 | 14.85% | -30.67% | 0.88 |

Relative to the ETF risk-budget baseline, the stock momentum strategy earns roughly 10.0 percentage points more annualized return. Relative to the same-universe equal-weight benchmark, however, the spread is only about 2.7 percentage points. This is the healthier comparison because it shows that the relevant question is not whether equity momentum beats defensive ETF allocation, but whether it improves upon broad large-cap equity exposure drawn from the same constituent set.

Figure 1 reports the cumulative NAV comparison and Figure 2 reports drawdowns.

### 5.2 Walk-forward evidence

Table 2 reports the walk-forward summary.

| Strategy | Window Count | Median CAGR | Worst CAGR | Worst MDD | Median Sharpe |
| --- | ---: | ---: | ---: | ---: | ---: |
| US ETF RiskBudget | 5 | 6.34% | -2.52% | -14.05% | 0.77 |
| US Same-Universe EW Benchmark | 5 | 19.19% | 4.04% | -35.80% | 0.87 |
| US Residual Sector Rotation | 5 | 11.51% | -1.03% | -32.79% | 0.83 |
| US Stock Mom12_1 | 5 | 20.38% | 3.29% | -30.67% | 0.83 |

The stock momentum strategy remains positive in every walk-forward window, which is encouraging. But the same-universe equal-weight benchmark also remains positive in every window. This result narrows the economic claim: the stock strategy appears to offer an incremental improvement within the same universe rather than a dramatic transformation of the opportunity set.

Figure 5 visualizes walk-forward CAGR by test window.

### 5.3 Transaction-cost evidence

Table 3 reports the current one-way cost grid.

| One-way cost (bps) | CAGR | MDD | Sharpe |
| --- | ---: | ---: | ---: |
| 5 | 14.97% | -30.66% | 0.88 |
| 7 | 14.85% | -30.67% | 0.88 |
| 10 | 14.67% | -30.68% | 0.87 |
| 15 | 14.37% | -30.70% | 0.85 |
| 25 | 13.77% | -30.75% | 0.82 |

The slope of performance erosion is moderate rather than catastrophic. Figure 3 shows that the tested strategy does not collapse under this range of transaction-cost assumptions.

### 5.4 Break-even cost analysis

Relative to the same-universe equal-weight benchmark, the estimated one-way break-even cost is about `42.8 bps` when defined as the transaction-cost level that drives the stock strategy's CAGR advantage to zero. Under a simpler mean daily excess-return approximation, the corresponding break-even level is about `52.5 bps`.

These numbers sit materially above the currently tested `7 bps` one-way assumption. They do not prove that the strategy is immune to implementation mistakes, but they do suggest that moderate cost misspecification is unlikely to overturn the basic return ranking relative to the same-universe benchmark.

### 5.5 Capital feasibility

The current whole-share implementation analysis indicates that about `17,462 USD` is required to hold at least one share of every target position. At `5,000 USD`, only `11` holdings are implementable, whereas at `20,000 USD`, the full `20` target holdings become feasible. This is a practically relevant result because equal-weight simplicity in the backtest does not guarantee exact implementability in smaller accounts.

### 5.6 Capacity diagnostics

Capacity diagnostics based on 60-day median dollar volume identify the tightest bottleneck in `EXC` on `2016-10-31`. At a `0.1%` participation threshold, implied strategy capacity is about `2.2M USD`. At `0.5%`, it is about `11.1M USD`. At `1.0%`, it is about `22.2M USD`.

These values imply that the strategy is plausible for smaller separate accounts and research-scale capital, but should not be portrayed as infinitely scalable simply because it trades large-cap equities. Figure 4 plots capacity against the participation threshold.

### 5.7 Factor regressions

The factor-regression results materially sharpen the interpretation of the raw-return evidence. The stock momentum strategy shows positive intercepts across specifications, but the alpha is not statistically significant at conventional levels once standard factors are included with Newey-West correction. In the strongest current specification, `FF5 + UMD`, the strategy produces `AlphaAnnual ≈ 2.25%` with `AlphaTstatNW ≈ 1.16`.

By contrast, the loading on `UMD` is strongly positive at about `0.27` with a very large t-statistic. This is exactly what one would expect from a long-only momentum portfolio. Therefore, the empirical message is not that the paper discovers a new source of alpha beyond known factor structure. Rather, it shows that a constrained, implementable portfolio architecture can retain economically meaningful momentum exposure after realistic frictions are imposed.

### 5.8 Interpretation

Taken together, the results support four conclusions.

First, a transparent large-cap `12-1` momentum strategy remains economically attractive after sector caps, liquidity filters, and explicit trading costs are imposed.

Second, the same-universe equal-weight benchmark is the most informative comparator, and it narrows the claim substantially. The momentum portfolio is better described as an incremental improvement over broad large-cap equity exposure than as a dramatic standalone alpha engine.

Third, the cost and capacity diagnostics make the strategy look plausible for moderate capital levels. The strategy is not obviously too fragile for real implementation, but it is also not capacity-free.

Fourth, the factor regressions imply that the paper should be positioned as an implementation study rather than a factor-discovery paper. That is the correct academic framing for the current evidence.

## 6. Limitations

The main remaining limitation is the quality of the constituent-history source. The current point-in-time universe is based on Wikipedia revision snapshots and is therefore still an approximation. This is materially better than the earlier static present-day membership file, but still weaker than an institutional constituent-history database with authoritative delisting-return treatment.

A second limitation is the lack of an explicit next-open or VWAP execution model. Current returns are still based on daily price series and do not yet model the micro-timing of implementation in enough detail for a top-tier empirical asset-pricing paper.

A third limitation is that the factor-adjusted alpha is not statistically strong in the current regressions. This does not invalidate the implementation contribution, but it prevents the paper from making stronger claims about abnormal performance beyond known momentum exposure.

Finally, the current cost model remains a simplification. Although break-even cost and participation-rate diagnostics are now included, a richer market-impact model would strengthen the final submission.

## 7. Conclusion

This paper studies whether a canonical `12-1` momentum signal can survive the transition from a frictionless academic idea to a realistically implementable portfolio design in U.S. large-cap equities. Under the current point-in-time approximation, the answer is broadly yes in economic terms. The constrained momentum strategy outperforms all tested benchmarks on raw CAGR, remains positive across all walk-forward windows, and does not appear fragile under moderate trading-cost assumptions. It also exhibits practical but limited capacity.

At the same time, the evidence narrows the correct claim. Relative to a same-universe equal-weight benchmark, the return advantage is positive but not enormous. Factor regressions indicate that the strategy is best understood as a disciplined implementation of momentum exposure rather than a discovery of strong independent alpha beyond known factor structure.

Accordingly, the contribution of the paper is implementation-focused. Its value lies in showing what remains of momentum after sector concentration limits, liquidity screens, transaction costs, and capital constraints are imposed together. If the final submission replaces the current point-in-time approximation with a stronger constituent-history source and improves execution modeling, the paper would have a credible position as a JDQS submission in quantitative portfolio management.

## Figure And Table Callouts

### Tables

- Table 1: Full-sample performance comparison
- Table 2: Walk-forward performance summary
- Table 3: Cost sensitivity grid
- Table 4: Break-even cost summary
- Table 5: Capital feasibility summary
- Table 6: Capacity summary
- Table 7: Factor regression summary

### Figures

- Figure 1: Cumulative NAV
  - `docs/figures_us_momentum_20260329/figure_1_cumulative_nav.png`
- Figure 2: Drawdown
  - `docs/figures_us_momentum_20260329/figure_2_drawdown.png`
- Figure 3: CAGR versus one-way cost
  - `docs/figures_us_momentum_20260329/figure_3_cost_curve.png`
- Figure 4: Capacity versus participation threshold
  - `docs/figures_us_momentum_20260329/figure_4_capacity_curve.png`
- Figure 5: Walk-forward CAGR by window
  - `docs/figures_us_momentum_20260329/figure_5_walkforward_cagr.png`

## Reproducibility Notes

The current core scripts used in the research build are:

- `tools/research/us_sp100_membership_wiki.py`
- `tools/data_ingestion/us_stock_sp100_backfill.py`
- `tools/research/us_stock_mom12_1.py`
- `tools/research/us_etf_riskbudget.py`
- `tools/research/us_residual_sector_rotation.py`
- `tools/research/us_momentum_eval.py`
- `tools/plotting/plot_us_momentum_paper_figures.py`

The current core output files used in this draft are:

- `backtests/us_sp100_membership_wiki_intervals.csv`
- `backtests/us_stock_sp100_universe_pitwiki.csv`
- `backtests/us_momentum_eval_pitwiki_20260329/us_compare.csv`
- `backtests/us_momentum_eval_pitwiki_20260329/us_walkforward_summary.csv`
- `backtests/us_momentum_eval_pitwiki_20260329/us_stock_mom12_1_cost.csv`
- `backtests/us_momentum_eval_pitwiki_20260329/us_stock_mom12_1_break_even_cost.csv`
- `backtests/us_momentum_eval_pitwiki_20260329/us_stock_mom12_1_capacity_summary.csv`
- `backtests/us_momentum_eval_pitwiki_20260329/us_factor_regressions.csv`

## References

Amihud, Y. (2002). Illiquidity and stock returns: Cross-section and time-series effects. *Journal of Financial Markets, 5*(1), 31-56.

Carhart, M. M. (1997). On persistence in mutual fund performance. *The Journal of Finance, 52*(1), 57-82. https://doi.org/10.1111/j.1540-6261.1997.tb03808.x

Jegadeesh, N., & Titman, S. (1993). Returns to buying winners and selling losers: Implications for stock market efficiency. *The Journal of Finance, 48*(1), 65-91. https://doi.org/10.1111/j.1540-6261.1993.tb04702.x

Korajczyk, R. A., & Sadka, R. (2004). Are momentum profits robust to trading costs? *The Journal of Finance, 59*(3), 1039-1082.

Lesmond, D. A., Schill, M. J., & Zhou, C. (2004). The illusory nature of momentum profits. *Journal of Financial Economics, 71*(2), 349-380. https://doi.org/10.1016/S0304-405X(03)00206-X

Moskowitz, T. J., & Grinblatt, M. (1999). Do industries explain momentum? *The Journal of Finance, 54*(4), 1249-1290. https://doi.org/10.1111/0022-1082.00146

Novy-Marx, R., & Velikov, M. (2016). A taxonomy of anomalies and their trading costs. *The Review of Financial Studies, 29*(1), 104-147. https://doi.org/10.1093/rfs/hhv063

Pastor, L., & Stambaugh, R. F. (2003). Liquidity risk and expected stock returns. *Journal of Political Economy, 111*(3), 642-685.

Shumway, T. (1997). The delisting bias in CRSP data. *The Journal of Finance, 52*(1), 327-340.
