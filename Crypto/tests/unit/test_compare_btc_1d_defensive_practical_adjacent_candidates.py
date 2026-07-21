from __future__ import annotations

from scripts.compare_btc_1d_defensive_practical_adjacent_candidates import build_report


def test_compare_btc_1d_defensive_practical_adjacent_candidates_ranks_pullthrough_first() -> None:
    report = build_report()
    assert report["candidate_count"] == 2
    assert report["top_practical_adjacent_candidate"] == "volatility_expansion_pullthrough_shorter_hold"


def test_compare_btc_1d_defensive_practical_adjacent_candidates_marks_void_refill_candidate_stage_hold() -> None:
    report = build_report()
    lookup = {row["label"]: row for row in report["ranked_candidates"]}
    assert lookup["shallow_liquidity_void_refill_continuation_reference"]["candidate_stage_evidence"] is True
    assert lookup["shallow_liquidity_void_refill_continuation_reference"]["practical_adjacent_status"] == "candidate_stage_hold"
