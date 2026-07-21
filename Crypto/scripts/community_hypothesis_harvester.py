from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


INPUT_EXTENSIONS = {".txt", ".md", ".jsonl"}
FAILED_AXIS_TERMS = {
    "trend",
    "breakout",
    "momentum",
    "top-20",
    "top20",
    "alt basket",
    "basket",
}


@dataclass(frozen=True)
class HypothesisItem:
    source: str
    raw_title_or_snippet: str
    market_universe: str
    holding_style: str
    signal_type: str
    claimed_edge_rationale: str
    required_data: list[str]
    expected_trade_frequency: str
    obvious_risks_caveats: list[str]
    confidence_quality_tag: str
    cluster_id: str
    novelty_status: str
    novelty_reason: str
    usefulness_score: float


RESEARCH_HISTORY_REGISTRY: list[dict[str, Any]] = [
    {
        "status": "duplicate_failed",
        "reason": "Overlaps with already-failed KRW top-20 alt short-term trend/breakout axis.",
        "match": {
            "market_universe": {"Altcoin basket"},
            "signal_type": {"trend / breakout"},
        },
    },
    {
        "status": "duplicate_failed",
        "reason": "Overlaps with already-failed KRW-BTC 4h EMA trend-following axis.",
        "match": {
            "market_universe": {"KRW-BTC single asset"},
            "signal_type": {"trend / breakout"},
        },
    },
    {
        "status": "duplicate_failed",
        "reason": "Overlaps with already-failed KRW-BTC 1h mean-reversion MVP axis.",
        "match": {
            "market_universe": {"KRW-BTC single asset"},
            "signal_type": {"non-trend mean reversion"},
            "required_data_any": {"ohlcv"},
        },
    },
    {
        "status": "descriptive_only_overlap",
        "reason": "Overlaps with Candidate Alpha, which is frozen as descriptive-only cross-market dislocation context.",
        "match": {
            "market_universe": {"KRW-BTC single asset"},
            "signal_type": {"cross-market dislocation"},
            "required_data_any": {"cross-venue price series"},
        },
    },
]


def _truncate(text: str, length: int = 160) -> str:
    compact = " ".join(text.split())
    return compact if len(compact) <= length else compact[: length - 3] + "..."


def _normalize_text(text: str) -> str:
    return " ".join(text.replace("\r", "\n").split())


def _load_text_items(path: Path) -> list[dict[str, str]]:
    if path.is_file():
        return _load_text_items_from_file(path)

    items: list[dict[str, str]] = []
    for child in sorted(path.rglob("*")):
        if child.is_file() and child.suffix.lower() in INPUT_EXTENSIONS:
            items.extend(_load_text_items_from_file(child))
    if not items:
        raise FileNotFoundError(f"No supported text items found under {path}")
    return items


def _load_text_items_from_file(path: Path) -> list[dict[str, str]]:
    if path.suffix.lower() == ".jsonl":
        rows = []
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            payload = json.loads(stripped)
            rows.append(
                {
                    "source": str(payload.get("source", path.name)),
                    "text": str(payload.get("text", "")),
                    "title": str(payload.get("title", "")),
                }
            )
        return rows

    raw_text = path.read_text(encoding="utf-8")
    return [{"source": path.name, "text": raw_text, "title": path.stem}]


def _detect_market_universe(text: str) -> str:
    lowered = text.lower()
    if "krw-btc" in lowered or "korean premium" in lowered or "kimchi premium" in lowered:
        return "KRW-BTC single asset"
    if "btc" in lowered and ("eth" in lowered or "major" in lowered):
        return "BTC and major crypto pair subset"
    if "alt" in lowered and "basket" in lowered:
        return "Altcoin basket"
    if "bitcoin" in lowered or "btc" in lowered:
        return "BTC single asset"
    return "Unspecified crypto market"


def _detect_holding_style(text: str) -> str:
    lowered = text.lower()
    if "minutes" in lowered or "intraday" in lowered or "same day" in lowered:
        return "intraday tactical"
    if "swing" in lowered or "1h" in lowered or "4h" in lowered:
        return "swing"
    if "cash" in lowered or "flat" in lowered or "wait" in lowered:
        return "cash-first selective exposure"
    return "selective discretionary hold"


def _detect_signal_type(text: str) -> str:
    lowered = text.lower()
    if any(term in lowered for term in ["premium", "basis", "dislocation", "spread"]):
        return "cross-market dislocation"
    if any(term in lowered for term in ["mean reversion", "oversold", "overbought", "revert", "snap back"]):
        return "non-trend mean reversion"
    if any(term in lowered for term in ["event", "listing", "news", "headline", "unlock"]):
        return "event-driven reaction"
    if (
        "funding" in lowered
        or "open interest" in lowered
        or "liquidation" in lowered
        or re.search(r"\boi\b", lowered)
    ):
        return "derivatives positioning stress"
    if any(term in lowered for term in ["trend", "breakout", "momentum"]):
        return "trend / breakout"
    return "other / unclear"


def _extract_required_data(text: str, signal_type: str) -> list[str]:
    lowered = text.lower()
    data: list[str] = []
    if "ohlcv" in lowered or any(term in lowered for term in ["rsi", "bollinger", "sma", "ema", "price"]):
        data.append("ohlcv")
    if any(term in lowered for term in ["premium", "basis", "spread", "krw-usdt", "binance", "bithumb"]):
        data.append("cross-venue price series")
    if any(term in lowered for term in ["news", "headline", "listing", "unlock"]):
        data.append("event calendar / headlines")
    if (
        "funding" in lowered
        or "open interest" in lowered
        or "liquidation" in lowered
        or re.search(r"\boi\b", lowered)
    ):
        data.append("derivatives metrics")
    if not data:
        if signal_type == "cross-market dislocation":
            data = ["cross-venue price series"]
        elif signal_type == "non-trend mean reversion":
            data = ["ohlcv"]
        else:
            data = ["manual text review"]
    return sorted(set(data))


def _detect_expected_trade_frequency(text: str) -> str:
    lowered = text.lower()
    if any(term in lowered for term in ["every day", "daily", "many trades", "frequent"]):
        return "high"
    if any(term in lowered for term in ["few", "occasional", "weekly", "rare"]):
        return "low"
    if any(term in lowered for term in ["1h", "4h", "swing"]):
        return "medium"
    return "unknown"


def _extract_rationale(text: str, signal_type: str) -> str:
    compact = _normalize_text(text)
    if signal_type == "cross-market dislocation":
        return "Public hypothesis claims local/global price dislocation or premium extremes contain regime information or mean-revert."
    if signal_type == "non-trend mean reversion":
        return "Public hypothesis claims short-term overextension normalizes faster than trend continuation."
    if signal_type == "event-driven reaction":
        return "Public hypothesis claims event-driven overshoot creates a testable post-event normalization or drift window."
    if signal_type == "derivatives positioning stress":
        return "Public hypothesis claims crowded positioning and liquidation stress distort short-horizon returns."
    if signal_type == "trend / breakout":
        return "Public hypothesis claims continuation after momentum or breakout."
    return _truncate(compact)


def _extract_risks(text: str, signal_type: str, market_universe: str) -> list[str]:
    risks: list[str] = []
    lowered = text.lower()
    if "execution" in lowered or "slippage" in lowered:
        risks.append("execution sensitivity")
    if "krw" in lowered or "premium" in lowered:
        risks.append("venue-specific distortion")
    if signal_type == "trend / breakout":
        risks.append("overlaps with already-failed trend/breakout axis")
    if signal_type == "event-driven reaction":
        risks.append("event labeling quality may dominate results")
    if signal_type == "derivatives positioning stress":
        risks.append("depends on external derivatives data quality")
    if market_universe == "Altcoin basket":
        risks.append("universe drift and crowding")
    if not risks:
        risks.append("hypothesis wording may be underspecified")
    return sorted(set(risks))


def _quality_tag(signal_type: str, required_data: list[str], market_universe: str) -> str:
    if signal_type == "trend / breakout":
        return "low"
    if market_universe == "Altcoin basket":
        return "medium"
    if required_data == ["ohlcv"] or required_data == ["cross-venue price series"]:
        return "high"
    if len(required_data) <= 2:
        return "medium"
    return "low"


def _cluster_signature(market_universe: str, signal_type: str, required_data: list[str]) -> str:
    base = f"{market_universe.lower()}|{signal_type.lower()}|{'/'.join(required_data)}"
    simplified = re.sub(r"[^a-z0-9|/]+", "-", base).strip("-")
    return simplified


def _usefulness_score(
    market_universe: str,
    signal_type: str,
    required_data: list[str],
    expected_trade_frequency: str,
    risks: list[str],
    quality_tag: str,
    novelty_status: str,
) -> float:
    score = 0.0
    if signal_type in {"non-trend mean reversion", "cross-market dislocation", "event-driven reaction"}:
        score += 3.0
    if "ohlcv" in required_data or "cross-venue price series" in required_data:
        score += 2.0
    if len(required_data) <= 2:
        score += 1.0
    if market_universe in {"KRW-BTC single asset", "BTC single asset"}:
        score += 1.5
    if expected_trade_frequency in {"low", "medium"}:
        score += 0.5
    if quality_tag == "high":
        score += 1.0
    if any(term in signal_type for term in ["trend", "breakout"]):
        score -= 3.0
    if market_universe == "Altcoin basket":
        score -= 1.5
    if any("already-failed" in risk for risk in risks):
        score -= 1.5
    if "derivatives metrics" in required_data:
        score -= 0.5
    if novelty_status == "novel_candidate":
        score += 2.0
    elif novelty_status == "duplicate_active":
        score -= 1.0
    elif novelty_status == "descriptive_only_overlap":
        score -= 2.0
    elif novelty_status == "duplicate_failed":
        score -= 4.0
    return round(score, 4)


def _matches_rule(
    rule: dict[str, Any],
    market_universe: str,
    signal_type: str,
    required_data: list[str],
) -> bool:
    match = rule["match"]
    if "market_universe" in match and market_universe not in match["market_universe"]:
        return False
    if "signal_type" in match and signal_type not in match["signal_type"]:
        return False
    if "required_data_any" in match and not set(required_data).intersection(match["required_data_any"]):
        return False
    return True


def classify_novelty(
    market_universe: str,
    signal_type: str,
    required_data: list[str],
) -> tuple[str, str]:
    for rule in RESEARCH_HISTORY_REGISTRY:
        if _matches_rule(rule, market_universe, signal_type, required_data):
            return rule["status"], rule["reason"]
    return "novel_candidate", "No direct overlap with failed or frozen research axes."


def parse_hypothesis_item(item: dict[str, str]) -> HypothesisItem:
    text = _normalize_text(item.get("text", ""))
    title = _normalize_text(item.get("title", "")) or _truncate(text, 120)
    market_universe = _detect_market_universe(text)
    holding_style = _detect_holding_style(text)
    signal_type = _detect_signal_type(text)
    required_data = _extract_required_data(text, signal_type)
    expected_trade_frequency = _detect_expected_trade_frequency(text)
    risks = _extract_risks(text, signal_type, market_universe)
    quality_tag = _quality_tag(signal_type, required_data, market_universe)
    cluster_id = _cluster_signature(market_universe, signal_type, required_data)
    novelty_status, novelty_reason = classify_novelty(
        market_universe,
        signal_type,
        required_data,
    )
    usefulness_score = _usefulness_score(
        market_universe,
        signal_type,
        required_data,
        expected_trade_frequency,
        risks,
        quality_tag,
        novelty_status,
    )
    return HypothesisItem(
        source=item.get("source", "unknown"),
        raw_title_or_snippet=title or _truncate(text),
        market_universe=market_universe,
        holding_style=holding_style,
        signal_type=signal_type,
        claimed_edge_rationale=_extract_rationale(text, signal_type),
        required_data=required_data,
        expected_trade_frequency=expected_trade_frequency,
        obvious_risks_caveats=risks,
        confidence_quality_tag=quality_tag,
        cluster_id=cluster_id,
        novelty_status=novelty_status,
        novelty_reason=novelty_reason,
        usefulness_score=usefulness_score,
    )


def cluster_hypotheses(hypotheses: list[HypothesisItem]) -> list[dict[str, Any]]:
    grouped: dict[str, list[HypothesisItem]] = defaultdict(list)
    for item in hypotheses:
        grouped[item.cluster_id].append(item)

    clusters: list[dict[str, Any]] = []
    for cluster_id, items in grouped.items():
        source_count = len({item.source for item in items})
        avg_score = sum(item.usefulness_score for item in items) / len(items)
        signal_mode = Counter(item.signal_type for item in items).most_common(1)[0][0]
        market_mode = Counter(item.market_universe for item in items).most_common(1)[0][0]
        holding_mode = Counter(item.holding_style for item in items).most_common(1)[0][0]
        quality_mode = Counter(item.confidence_quality_tag for item in items).most_common(1)[0][0]
        novelty_mode = Counter(item.novelty_status for item in items).most_common(1)[0][0]
        novelty_reason = Counter(item.novelty_reason for item in items).most_common(1)[0][0]
        data_union = sorted({field for item in items for field in item.required_data})
        risks = Counter(risk for item in items for risk in item.obvious_risks_caveats).most_common(3)
        clusters.append(
            {
                "cluster_id": cluster_id,
                "cluster_size": len(items),
                "source_count": source_count,
                "representative_problem_definition": {
                    "market_universe": market_mode,
                    "holding_style": holding_mode,
                    "signal_type": signal_mode,
                    "required_data": data_union,
                    "confidence_quality_tag": quality_mode,
                    "novelty_status": novelty_mode,
                },
                "novelty_reason": novelty_reason,
                "claimed_edge_summary": Counter(item.claimed_edge_rationale for item in items).most_common(1)[0][0],
                "obvious_risks_caveats": [risk for risk, _ in risks],
                "average_usefulness_score": round(avg_score, 4),
                "example_snippets": [item.raw_title_or_snippet for item in items[:3]],
            }
        )

    clusters.sort(
        key=lambda item: (
            {
                "novel_candidate": 0,
                "duplicate_active": 1,
                "descriptive_only_overlap": 2,
                "duplicate_failed": 3,
            }[item["representative_problem_definition"]["novelty_status"]],
            -item["average_usefulness_score"],
            -item["cluster_size"],
            -item["source_count"],
            item["cluster_id"],
        )
    )
    return clusters


def build_report(hypotheses: list[HypothesisItem], clusters: list[dict[str, Any]]) -> dict[str, Any]:
    top_candidates = []
    for rank, cluster in enumerate(clusters[:3], start=1):
        top_candidates.append(
            {
                "rank": rank,
                "cluster_id": cluster["cluster_id"],
                "problem_definition_candidate": cluster["representative_problem_definition"],
                "why_useful_for_research": (
                    "Structurally testable and materially different from the already-failed short-term trend/breakout axis"
                    if cluster["representative_problem_definition"]["novelty_status"] == "novel_candidate"
                    else cluster["novelty_reason"]
                ),
                "average_usefulness_score": cluster["average_usefulness_score"],
                "source_count": cluster["source_count"],
                "cluster_size": cluster["cluster_size"],
                "novelty_status": cluster["representative_problem_definition"]["novelty_status"],
                "example_snippets": cluster["example_snippets"],
            }
        )

    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "boundary": {
            "what_it_does": "Harvests public community hypotheses and normalizes them into problem-definition candidates for research triage.",
            "what_it_does_not_do": "Does not generate trading signals, execution logic, runtime integration, or deployable alpha claims.",
        },
        "input_summary": {
            "hypothesis_count": len(hypotheses),
            "cluster_count": len(clusters),
            "sources": sorted({item.source for item in hypotheses}),
            "novelty_counts": dict(Counter(item.novelty_status for item in hypotheses)),
        },
        "top_problem_definition_candidates": top_candidates,
        "all_clusters": clusters,
        "all_hypotheses": [asdict(item) for item in hypotheses],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Community Hypothesis Harvester Report",
        "",
        "## Boundary",
        f"- does: {report['boundary']['what_it_does']}",
        f"- does_not_do: {report['boundary']['what_it_does_not_do']}",
        "",
        "## Input Summary",
        f"- hypothesis_count: {report['input_summary']['hypothesis_count']}",
        f"- cluster_count: {report['input_summary']['cluster_count']}",
        f"- sources: {report['input_summary']['sources']}",
        f"- novelty_counts: {report['input_summary']['novelty_counts']}",
        "",
        "## Top Problem-Definition Candidates",
    ]
    for candidate in report["top_problem_definition_candidates"]:
        definition = candidate["problem_definition_candidate"]
        lines.extend(
            [
                f"### Rank {candidate['rank']}: {candidate['cluster_id']}",
                f"- market_universe: {definition['market_universe']}",
                f"- holding_style: {definition['holding_style']}",
                f"- signal_type: {definition['signal_type']}",
                f"- required_data: {definition['required_data']}",
                f"- confidence_quality_tag: {definition['confidence_quality_tag']}",
                f"- novelty_status: {candidate['novelty_status']}",
                f"- average_usefulness_score: {candidate['average_usefulness_score']}",
                f"- why_useful_for_research: {candidate['why_useful_for_research']}",
                f"- example_snippets: {candidate['example_snippets']}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def run_harvester(input_path: Path, output_dir: Path) -> dict[str, Any]:
    items = _load_text_items(input_path)
    hypotheses = [parse_hypothesis_item(item) for item in items]
    clusters = cluster_hypotheses(hypotheses)
    report = build_report(hypotheses, clusters)

    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = output_dir / f"community_hypothesis_harvest_{stamp}.json"
    md_path = output_dir / f"community_hypothesis_harvest_{stamp}.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return {
        "report_json_path": json_path,
        "report_md_path": md_path,
        "report": report,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Harvest public community crypto hypotheses into structured research candidates."
    )
    parser.add_argument("--input-path", required=True)
    parser.add_argument("--output-dir", default="analysis_results")
    args = parser.parse_args()

    artifacts = run_harvester(Path(args.input_path), Path(args.output_dir))
    print(
        json.dumps(
            {
                "report_json_path": str(artifacts["report_json_path"]),
                "report_md_path": str(artifacts["report_md_path"]),
                "top_problem_definition_candidates": artifacts["report"]["top_problem_definition_candidates"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
