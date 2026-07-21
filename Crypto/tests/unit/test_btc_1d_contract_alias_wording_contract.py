from __future__ import annotations

import json

from scripts.btc_1d_contract_health_constants import (
    HEALTH_ORDER_ALIAS,
    HEALTH_ORDER_DEPRECATION_MESSAGE,
)
from scripts.check_btc_1d_contract_health import check_contract_health
from scripts.compare_btc_1d_meta_contract_screen import build_report


def test_contract_alias_wording_is_shared_across_contract_outputs(tmp_path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "standard_check_order": ["practical", "research", "contract", "brief"],
        "quick_read_order_version": "operating_v3",
        "quick_read_order": ["practical_status", "combined_health", "quick_read_contract", "open_first"],
        "regression_lock_test": "tests/unit/test_btc_1d_operating_cli_help_contract.py",
    }
    (analysis_dir / "btc_1d_operating_brief_latest.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    (analysis_dir / "btc_1d_operating_index_latest.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    (analysis_dir / "btc_1d_quick_read_contract_screen_latest.json").write_text(
        json.dumps(
            {
                "report": {
                    "regression_lock_test": payload["regression_lock_test"],
                    "contract_summary": {
                        "operating_brief_version": "operating_v3",
                        "operating_index_version": "operating_v3",
                        "research_stack_version": "research_stack_v2",
                        "operating_contract_aligned": True,
                        "research_contract_distinct": True,
                        "shared_standard_check_order": payload["standard_check_order"],
                    },
                    "contract_verdict": {
                        "contracts_are_well_partitioned": True,
                        "preferred_operating_contract_version": "operating_v3",
                        "preferred_research_contract_version": "research_stack_v2",
                    },
                }
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (analysis_dir / "btc_1d_research_stack_operating_brief_latest.json").write_text(
        json.dumps(
            {
                "regression_lock_test": payload["regression_lock_test"],
                "standard_check_order_reference": payload["standard_check_order"],
                "quick_read_order_version": "research_stack_v2",
                "operating_brief": {},
                "models": {},
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (analysis_dir / "btc_1d_practical_promotion_gate_latest.json").write_text(
        json.dumps(
            {
                "ok": True,
                "status_label": "btc_only_practical_with_caveats",
                "candidate": "candidate_a",
                "scope": "BTC-only",
                "caveats": [],
                "carry_metrics": {"sharpe": 1.0, "cagr": 0.3, "max_drawdown": 0.1},
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    contract_health = check_contract_health(analysis_dir=analysis_dir)
    meta_contract = build_report(analysis_dir=analysis_dir)

    assert contract_health["deprecated_fields"][HEALTH_ORDER_ALIAS] == HEALTH_ORDER_DEPRECATION_MESSAGE
    assert (
        meta_contract["meta_contract_summary"]["deprecated_aliases"][HEALTH_ORDER_ALIAS]
        == HEALTH_ORDER_DEPRECATION_MESSAGE
    )
