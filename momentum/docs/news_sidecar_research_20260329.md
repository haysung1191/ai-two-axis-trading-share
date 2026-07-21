# News Sidecar Research

Purpose:

- build a simple, explainable news sidecar for both Korea and US tracks
- keep it separate from the main alpha engines
- use it first as a research filter, not as a standalone engine

## US

Source:

- Hugging Face dataset:
  - [KrossKinetic/SP500-Financial-News-Articles-Time-Series](https://hf.co/datasets/KrossKinetic/SP500-Financial-News-Articles-Time-Series)

Implementation:

- script:
- [us_news_hf_sidecar.py](/C:/AI/momentum/tools/research/us_news_hf_sidecar.py)
- output base:
  - `data\news_us_hf`
- coverage:
  - [us_news_sidecar_coverage.csv](D:\AI\모멘텀 투자\backtests\us_news_sidecar_coverage.csv)
- signal sanity:
  - [us_news_sidecar_signal_eval.csv](D:\AI\모멘텀 투자\backtests\us_news_sidecar_signal_eval.csv)

Fields:

- `article_count`
- `positive_hits`
- `negative_hits`
- `title_score`

Notes:

- this is attachable to the current US stock universe because it has `symbol` and `Publishdate`
- current build uses a transparent keyword score, not transformer inference
- current dataset is too sparse for trading evaluation
- current conclusion is not "weak signal"; it is **`INSUFFICIENT_COVERAGE`**
- latest evaluation shows:
  - `AdequateCoverageDays = 1`
  - `AdequateCoverageRatio ≈ 0.00035`
  - `MedianCoveredNamesNonZero = 2`
- practical conclusion:
  - keep as research metadata only
  - do not attach it to the live US alpha engine in the current form

## Korea

HF stance:

- no immediately usable Korea finance-news dataset was found on HF
- finance-specific Korean sentiment on HF is weak
- generic Korean sentiment models exist, but they are not finance-specific

Implementation:

- Naver Finance headline fallback:
- [kis_news_backfill.py](/C:/AI/momentum/tools/data_ingestion/kis_news_backfill.py)
- output base:
  - `data\news_kis_naver`
- coverage:
  - [kis_news_sidecar_coverage.csv](D:\AI\모멘텀 투자\backtests\kis_news_sidecar_coverage.csv)
- signal sanity:
  - [kis_news_sidecar_signal_eval.csv](D:\AI\모멘텀 투자\backtests\kis_news_sidecar_signal_eval.csv)

Fields:

- `article_count`
- `positive_hits`
- `negative_hits`
- `title_score`

Notes:

- this is not a full NLP pipeline
- it is a research sidecar for headline pressure / headline polarity only
- if this proves useful, the next step is a finance-tuned Korean sentiment model
- current simple headline score is mixed:
  - `article_count` spread is negative
  - `title_score` spread is positive on the current sample
- practical conclusion:
  - Korea news has usable volume
  - but the keyword-only score is still research-only

## Current Verdict

- US:
  - keep `US Stock Mom12_1` as the main alpha track
  - keep HF news sidecar as optional research metadata only
- Korea:
  - keep `Weekly ETF RiskBudget` as the live-operating baseline
  - if news is explored further, use Naver headline data rather than HF
- next upgrade path:
  - US: earnings-event or revisions data
  - Korea: finance-tuned Korean sentiment model on Naver headlines
