# Deep Research Prompt

Use this prompt in the other thread if external literature and venue positioning help is needed.

---

I am preparing a finance paper for possible submission to `Journal of Derivatives and Quantitative Studies (JDQS)` or a comparable Korea/Asia quantitative finance journal.

Please do a focused literature and positioning review for this paper idea:

Working topic:
`Implementable 12-1 momentum in large-cap U.S. equities under sector caps, liquidity filters, transaction costs, and minimum-capital constraints`

Current empirical setup:
- stock universe: currently implemented as static current `S&P 100` membership
- signal: `12-1` momentum
- portfolio construction:
  - top 20 names
  - equal weight
  - max 3 names per sector
- liquidity filter: 60-day median dollar volume
- minimum price filter
- monthly rebalance
- transaction cost stress tested across 5, 7, 10, 15, 25 bps one-way
- benchmark 1: ETF risk-budget allocation
- benchmark 2: residual sector rotation ETF strategy
- current headline results:
  - stock momentum CAGR about `18.4%`
  - ETF risk-budget CAGR about `4.8%`
  - residual sector rotation CAGR about `7.4%`
  - walk-forward worst CAGR for stock momentum still positive
- current major limitation:
  - survivorship bias because the stock universe uses static current S&P 100 membership

What I need from you:

1. Find the most relevant papers on:
- cross-sectional momentum
- implementable or friction-aware momentum
- sector-neutral or sector-constrained momentum
- liquidity/capacity constraints in equity momentum
- retail or minimum-capital implementability in portfolio studies

2. For each important paper, give:
- citation
- 2-4 sentence summary
- why it is relevant to my paper
- whether it helps justify novelty, benchmark choice, or robustness tests

3. Assess whether this paper is a better fit for:
- `JDQS`
- `Korean Journal of Financial Studies`
- `Asia-Pacific Journal of Financial Studies`
- or another better-matched journal

4. Tell me exactly what I must add to clear the publication bar:
- mandatory fixes
- robustness tests
- factor regressions
- benchmark additions
- bias corrections

5. Propose a refined contribution statement that is honest and publishable:
- not "new factor discovery"
- more like "implementable momentum under real-world constraints"

6. Draft:
- one strong paper title
- one abstract of about 150-200 words
- one introduction outline
- one table list
- one figure list

7. If there are obvious fatal weaknesses, say them directly.

Important:
- prioritize primary or official sources where possible
- use recent and classic finance literature
- include links
- be specific about how to position the paper so it is not rejected as just another backtest

---

Expected output format:

- Venue recommendation
- Literature map
- Publication risks
- Required robustness checklist
- Revised contribution statement
- Draft title/abstract/outline

