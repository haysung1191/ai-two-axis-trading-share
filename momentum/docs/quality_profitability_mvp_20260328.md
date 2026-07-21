## Quality/Profitability MVP

### What Was Added
- `FnGuide` ratio-table sidecar pipeline
- `Weekly QualityProfitability MVP` named strategy
- stock-only, research-only
- point-in-time approximation using conservative effective dates:
  - annual `YYYY/12` -> `+90d`
  - quarterly `YYYY/Q` -> `+45d`

### Data Paths
- sidecar data: `data/quality_fnguide/stock/*.csv.gz`
- backfill report: `data/quality_fnguide/quality_backfill_report.csv`
- evaluation bundle: `backtests/quality_eval_20260328`

### Signal Construction
- positive:
  - `ROE`
  - `ROA`
  - `gross margin`
  - `operating margin`
  - `sales growth`
  - `EPS growth`
- negative:
  - `debt ratio`
- cross-sectional composite:
  - z-score blend over available metrics
- execution:
  - `Weekly`
  - `stock-only`
  - existing risk controls reused

### Current Result
- full available coverage:
  - `BaselineCAGR = 0.09876`
  - `BaselineMDD = -0.084859`
  - `Sharpe = 1.078208`
  - `CAGR_net_0.5pct = 0.08747`
- coverage:
  - `2022-03-31 ~ 2026-03-31`
- walkforward:
  - `WindowCount = 3`
  - `MedianCAGR = -0.001439`
  - `WorstCAGR = -0.106216`
  - `WorstMDD = -0.25371`

### Same-Coverage Benchmark Check
- on `2022-03-31+` only:
  - `Weekly QualityProfitability MVP`: `CAGR 0.212018`
  - `Weekly Score50 RegimeState`: `CAGR 0.199847`
  - `Weekly ETF RiskBudget`: `CAGR 0.141918`
  - `Weekly Hybrid QP50 RS50`: `CAGR 0.206862`, `MDD -0.073399`, `Sharpe 1.856770`

### Strict Walkforward Recheck
- using full price history for universe warmup and only restricting the test windows to quality-covered dates:
  - `Weekly QualityProfitability MVP`
    - `WindowCount = 2`
    - `MedianCAGR = -0.159038`
    - `WorstCAGR = -0.238901`
    - `WorstMDD = -0.279075`
  - `Weekly Hybrid QP50 RS50`
    - `WindowCount = 2`
    - `MedianCAGR = -0.064259`
    - `WorstCAGR = -0.118956`
    - `WorstMDD = -0.146548`
  - `Weekly Score50 RegimeState`
    - `MedianCAGR = 0.037818`
    - `WorstCAGR = 0.012918`
    - `WorstMDD = -0.064013`

### Interpretation
- promising recent-sample alpha
- not operational-ready
- the attractive same-coverage full-sample numbers do **not** survive strict OOS recheck
- still research-only because:
  - coverage is short
  - walkforward dispersion is high
  - worst OOS drawdown is too large

### Current Judgment
- `Weekly QualityProfitability MVP`: not promotable
- `Weekly Hybrid QP50 RS50`: not promotable
- keep both as archived research results, not active candidates

### Current Status
- keep `Weekly ETF RiskBudget` as operating baseline
- keep `Weekly QualityProfitability MVP` as research candidate
- next work should focus on:
  - wider quality history
  - more robust PIT mapping
  - OOS stability before any promotion
