from __future__ import annotations

import json

import pandas as pd

from research_lane_stage1.backtest.engine import run_account_backtest
from research_lane_stage1.families.bithumb.xs_momentum import generate_models as generate_bithumb_models
from research_lane_stage1.families.kis.combined_short_reversal import generate_models as generate_kis_models
from research_lane_stage1.persistence.artifacts import write_model_artifacts
from research_lane_stage1.persistence.queues import append_conversion_queue
from research_lane_stage1.persistence.registry import append_candidate_registry
from research_lane_stage1.persistence.handoff import has_complete_artifact_refs, pending_artifact_record, split_conversion_handoff


def _price_rows(symbols: list[str], account: str, price_field: str = "close") -> pd.DataFrame:
    dates = pd.date_range("2019-01-01", periods=900, freq="D")
    rows = []
    for offset, symbol in enumerate(symbols):
        for idx, date in enumerate(dates):
            price = 100.0 + idx * (1 + offset * 0.1)
            rows.append(
                {
                    "date": date,
                    "symbol": symbol,
                    "account": account,
                    "close": price,
                    "price_krw": price,
                }
            )
    return pd.DataFrame(rows)


def test_family_generators_create_account_level_models() -> None:
    b_models = generate_bithumb_models({"symbol_count": 34})
    k_models = generate_kis_models({"symbol_count": 11996})

    assert b_models[0]["candidate_type"] == "account_portfolio_model"
    assert b_models[0]["account"] == "BITHUMB_KRW"
    assert k_models[0]["account"] == "KIS_COMBINED_KRW"
    assert k_models[0]["portfolio"]["max_positions"] in {25, 50, 100}
    assert b_models[0]["safety"]["broker_submit_allowed"] is False


def test_account_backtest_outputs_required_account_artifacts(tmp_path) -> None:
    model = generate_bithumb_models({"symbol_count": 4}, {"lookback_days": [5], "top_n": [2], "rebalance_days": [7]})[0]
    prices = _price_rows(["AAA_KRW", "BBB_KRW", "CCC_KRW", "DDD_KRW"], "BITHUMB_KRW")

    result = run_account_backtest(model, prices)

    assert {"daily_equity", "daily_returns", "daily_weights", "daily_turnover", "simulated_research_trades", "metrics"} <= set(result)
    assert "CASH_KRW" in set(result["daily_weights"]["symbol"])
    weight_sums = result["daily_weights"].pivot_table(index="date", columns="symbol", values="weight", aggfunc="sum").fillna(0).sum(axis=1)
    assert float((weight_sums - 1.0).abs().max()) < 1e-9

    refs = write_model_artifacts(model, result, {"primary_class": "research_only"}, tmp_path)
    assert (tmp_path / model["model_id"] / "daily_equity.csv").exists()
    assert (tmp_path / model["model_id"] / "simulated_research_trades.csv").exists()
    metrics = json.loads((tmp_path / model["model_id"] / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["model_id"] == model["model_id"]


def test_append_only_registry_and_conversion_queue_guard(tmp_path) -> None:
    registry = tmp_path / "candidate_registry.jsonl"
    queue = tmp_path / "conversion_queue.jsonl"
    record = {
        "run_id": "r1",
        "model_id": "m1",
        "candidate_type": "account_portfolio_model",
        "primary_class": "conversion_candidate",
    }

    append_candidate_registry(record, registry)
    append_candidate_registry({**record, "run_id": "r2"}, registry)
    append_conversion_queue(record, queue)

    assert len(registry.read_text(encoding="utf-8").strip().splitlines()) == 2
    assert len(queue.read_text(encoding="utf-8").strip().splitlines()) == 1


def test_conversion_handoff_requires_full_artifact_refs(tmp_path) -> None:
    ready = {
        "model_id": "m_ready",
        "artifact_refs": {},
    }
    for key in ["daily_equity", "daily_returns", "daily_weights", "daily_turnover", "metrics", "classification", "model_definition"]:
        path = tmp_path / f"{key}.x"
        path.write_text("ok", encoding="utf-8")
        ready["artifact_refs"][key] = str(path)
    pending = {"model_id": "m_pending", "artifact_refs": {}}

    ready_records, pending_records = split_conversion_handoff([ready, pending])

    assert has_complete_artifact_refs(ready)
    assert len(ready_records) == 1
    assert len(pending_records) == 1
    assert pending_artifact_record(pending)["stage2_blocked_until_artifacts_exist"] is True
