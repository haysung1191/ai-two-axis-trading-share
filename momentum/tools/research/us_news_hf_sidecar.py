import argparse
import json
import os
from collections import defaultdict
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


import pandas as pd
from huggingface_hub import hf_hub_download

from news_sidecar_data import build_coverage_report, write_news_file


POSITIVE_WORDS = [
    "beat",
    "beats",
    "strong",
    "growth",
    "surge",
    "gain",
    "gains",
    "rally",
    "record",
    "upgrade",
    "upgrades",
    "raised",
    "outperform",
    "profit",
    "wins",
    "approval",
    "expansion",
]

NEGATIVE_WORDS = [
    "miss",
    "misses",
    "weak",
    "cut",
    "cuts",
    "downgrade",
    "downgrades",
    "drop",
    "drops",
    "fall",
    "falls",
    "slump",
    "warning",
    "probe",
    "lawsuit",
    "recall",
    "loss",
    "delay",
    "decline",
    "declines",
    "investigation",
]


def _score_title(title: str) -> tuple[int, int]:
    text = str(title).lower()
    pos = sum(text.count(word) for word in POSITIVE_WORDS)
    neg = sum(text.count(word) for word in NEGATIVE_WORDS)
    return pos, neg


def _load_target_symbols(universe_path: Path) -> set[str]:
    df = pd.read_csv(universe_path)
    col = "Symbol" if "Symbol" in df.columns else df.columns[0]
    return {str(x).strip().upper().replace(".", "-") for x in df[col].dropna().unique()}


def build_us_news_sidecar(repo_id: str, universe_path: Path, out_base: Path) -> pd.DataFrame:
    target_symbols = _load_target_symbols(universe_path)
    jsonl_path = hf_hub_download(repo_id=repo_id, repo_type="dataset", filename="stock_data_articles.jsonl")
    agg: dict[tuple[str, str], dict[str, float]] = defaultdict(lambda: {"article_count": 0.0, "positive_hits": 0.0, "negative_hits": 0.0})

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            symbol = str(row.get("symbol", "")).strip().upper().replace(".", "-")
            if symbol not in target_symbols:
                continue
            publishdate = str(row.get("Publishdate", "")).strip()
            if not publishdate:
                continue
            date_str = publishdate[:10]
            try:
                pd.Timestamp(date_str)
            except Exception:
                continue
            pos, neg = _score_title(row.get("Title", ""))
            bucket = agg[(symbol, date_str)]
            bucket["article_count"] += 1.0
            bucket["positive_hits"] += float(pos)
            bucket["negative_hits"] += float(neg)

    symbol_rows: dict[str, list[dict[str, float | str]]] = defaultdict(list)
    for (symbol, date_str), stats in agg.items():
        symbol_rows[symbol].append(
            {
                "date": date_str,
                "article_count": stats["article_count"],
                "positive_hits": stats["positive_hits"],
                "negative_hits": stats["negative_hits"],
                "title_score": stats["positive_hits"] - stats["negative_hits"],
            }
        )

    for symbol in sorted(target_symbols):
        rows = symbol_rows.get(symbol, [])
        df = pd.DataFrame(rows, columns=["date", "article_count", "positive_hits", "negative_hits", "title_score"])
        write_news_file(str(out_base / "stock" / f"{symbol}.csv.gz"), df)

    return build_coverage_report(str(out_base), market="stock")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build US stock news sidecar from Hugging Face S&P500 article dataset.")
    p.add_argument("--repo-id", type=str, default="KrossKinetic/SP500-Financial-News-Articles-Time-Series")
    p.add_argument("--universe-path", type=str, default="backtests/us_stock_sp100_universe.csv")
    p.add_argument("--out-base", type=str, default="data/news_us_hf")
    p.add_argument("--coverage-out", type=str, default="backtests/us_news_sidecar_coverage.csv")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    out_base = Path(args.out_base)
    out_base.mkdir(parents=True, exist_ok=True)
    (out_base / "stock").mkdir(parents=True, exist_ok=True)
    coverage = build_us_news_sidecar(args.repo_id, Path(args.universe_path), out_base)
    coverage.to_csv(args.coverage_out, index=False)
    print(coverage.head(20).to_string(index=False))
    print()
    print(f"saved coverage={args.coverage_out}")


if __name__ == "__main__":
    main()
