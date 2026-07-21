from __future__ import annotations

import json
from pathlib import Path

from scripts import compare_btc_1d_meta_contract_screen as meta_contract_screen


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_build_report_aligns_regression_lock_and_standard_order(tmp_path: Path) -> None:
    regression_lock = "tests/unit/test_btc_1d_operating_cli_help_contract.py"
    standard_order = ["practical", "research", "contract", "brief"]

    _write_json(
        tmp_path / "btc_1d_operating_brief_latest.json",
        {
            "regression_lock_test": regression_lock,
            "standard_check_order": standard_order,
        },
    )
    _write_json(
        tmp_path / "btc_1d_operating_index_latest.json",
        {
            "regression_lock_test": regression_lock,
            "standard_check_order": standard_order,
        },
    )
    _write_json(
        tmp_path / "btc_1d_quick_read_contract_screen_latest.json",
        {
            "report": {
                "regression_lock_test": regression_lock,
                "contract_summary": {
                    "shared_standard_check_order": standard_order,
                },
            }
        },
    )
    _write_json(
        tmp_path / "btc_1d_execution_contract_screen_latest.json",
        {
            "entries": [
                {
                    "label": "operating_brief",
                    "regression_lock_test": regression_lock,
                    "standard_check_order_reference": standard_order,
                },
                {
                    "label": "operating_index",
                    "regression_lock_test": regression_lock,
                    "standard_check_order_reference": standard_order,
                },
            ],
            "execution_contract_summary": {
                "regression_lock_test": regression_lock,
                "wording_regression_test": "tests/unit/test_btc_1d_execution_contract_wording_contract.py",
                "symmetry_regression_test": "tests/unit/test_btc_1d_execution_meta_summary_symmetry_contract.py",
                "standard_check_order_reference": standard_order,
                "execution_meta_quick_status": "execution+meta quick | execution=complete | meta=complete",
            },
        },
    )
    _write_json(
        tmp_path / "btc_1d_execution_meta_contract_test_index_latest.json",
        {
            "tests": [
                {
                    "label": "contract_read_order_runbook_contract",
                    "locks": [
                        "quick-read contract screen read order",
                        "execution contract screen read order",
                        "meta contract screen read order",
                        "execution meta contract test index read order",
                        "execution/meta contract test map reverse screen pointers",
                    ],
                }
            ],
            "summary": {
                "meta_contract_tests": [
                    "tests/unit/test_compare_btc_1d_meta_contract_screen.py",
                    "tests/unit/test_btc_1d_meta_contract_runbook_wording_contract.py",
                    "tests/unit/test_btc_1d_contract_read_order_runbook_contract.py",
                ]
            }
        },
    )
    _write_json(
        tmp_path / "btc_1d_practical_promotion_gate_latest.json",
        {
            "ok": True,
            "status_label": "btc_only_practical_with_caveats",
            "candidate": "candidate_a",
            "scope": "BTC-only",
            "caveats": [],
            "carry_metrics": {"sharpe": 1.0, "cagr": 0.3, "max_drawdown": 0.1},
        },
    )
    _write_json(
        tmp_path / "btc_1d_research_stack_operating_brief_latest.json",
        {
            "regression_lock_test": regression_lock,
            "standard_check_order_reference": standard_order,
            "quick_read_order_version": "research_stack_v2",
            "operating_brief": {
                "attack_frontier": "ratio112_tighter_stop_main",
                "attack_backup": "ratio111_tighter_stop_backup",
                "defensive_hold": "volatility_expansion_pullthrough_shorter_hold",
                "highest_priority_near_miss": "trend_dip_reversal_breakout_tighter_stop_mid_hold",
            },
            "models": {
                "attack_main": {"base_cagr": 0.4243, "base_mdd": 0.1609, "base_sharpe": 1.5613},
                "attack_backup": {"sensitivity_max_drift": 0.4172},
                "defensive_hold": {"status_label": "candidate_stage_hold"},
                "highest_priority_near_miss": {"candidate_stage_status": "validated_fail_hold"},
            },
        },
    )

    report = meta_contract_screen.build_report(tmp_path)

    summary = report["meta_contract_summary"]
    assert summary["shared_regression_lock_test"] == regression_lock
    assert summary["regression_lock_aligned"] is True
    assert summary["shared_standard_check_order"] == standard_order
    assert summary["standard_check_order_aligned"] is True
    assert summary["standard_check_order_scope"] == [
        "operating_brief",
        "operating_index",
        "quick_read_contract_screen",
        "execution_contract_screen",
        "research_stack_operating_brief",
        "practical_health",
        "research_stack_health",
        "contract_health",
        "execution_contract_screen_operating_brief_entry",
        "execution_contract_screen_operating_index_entry",
    ]
    assert summary["health_order_aligned"] is True
    assert summary["all_health_standard_order_aligned"] is True
    assert summary["execution_contract_entry_scope_included"] is True
    assert summary["execution_contract_wording_lock_included"] is True
    assert summary["execution_contract_symmetry_lock_included"] is True
    assert (
        summary["meta_contract_topline_regression_test"]
        == "tests/unit/test_btc_1d_meta_contract_wording_contract.py"
    )
    assert summary["meta_contract_topline_reason_wording_included"] is True
    assert (
        summary["meta_contract_topline_status"]
        == "meta topline status | regression_test=tests/unit/test_btc_1d_meta_contract_wording_contract.py | reason_included=True"
    )
    assert (
        summary["meta_contract_topline_quick_status"]
        == "meta topline quick | lock=ok | reason=included"
    )
    assert (
        summary["meta_contract_topline_highlight"]
        == "topline highlight | lock=ok | reason=included"
    )
    assert (
        summary["meta_contract_reason_highlight_summary"]
        == "reason+highlight | summary_ready | reason=included"
    )
    assert (
        summary["meta_contract_reason_final_verdict"]
        == "reason final verdict | complete | reason=included"
    )
    assert (
        summary["meta_contract_integrated_topline_verdict"]
        == "meta contract integrated | topline=complete | reason=complete"
    )
    assert (
        summary["execution_contract_symmetry_regression_test"]
        == "tests/unit/test_btc_1d_execution_meta_summary_symmetry_contract.py"
    )
    assert summary["execution_contract_symmetry_fields"] == [
        "symmetry_regression_test",
        "execution_contract_symmetry_lock_included",
        "execution_contract_symmetry_regression_test",
        "execution_meta_contract_test_index_symmetry_fields",
    ]
    assert summary["execution_contract_symmetry_field_set"] == [
        "symmetry_regression_test",
        "execution_contract_symmetry_lock_included",
        "execution_contract_symmetry_regression_test",
        "execution_meta_contract_test_index_symmetry_fields",
    ]
    assert (
        summary["execution_contract_symmetry_field_map"]
        == "symmetry field map | symmetry_regression_test | execution_contract_symmetry_lock_included | execution_contract_symmetry_regression_test | execution_meta_contract_test_index_symmetry_fields"
    )
    assert (
        summary["execution_contract_symmetry_contract_bundle"]
        == "symmetry contract bundle | symmetry_regression_test | execution_contract_symmetry_lock_included | execution_contract_symmetry_regression_test | execution_meta_contract_test_index_symmetry_fields"
    )
    assert summary["execution_contract_symmetry_ready"] is True
    assert (
        summary["execution_contract_symmetry_reason_scope"]
        == "symmetry reason scope | key | set | map | bundle | ready"
    )
    assert (
        summary["execution_contract_symmetry_reason_range_summary"]
        == "symmetry reason range | key | set | map | bundle | ready | stack_complete"
    )
    assert (
        summary["execution_contract_symmetry_reason_final_summary"]
        == "symmetry reason final | key | set | map | bundle | ready | stack_complete | summary_ready"
    )
    assert (
        summary["execution_contract_symmetry_status"]
        == "symmetry contract status | ready=True | symmetry reason scope | key | set | map | bundle | ready"
    )
    assert summary["execution_contract_symmetry_stack_complete"] is True
    assert summary["execution_contract_symmetry_summary_ready"] is True
    assert (
        summary["execution_contract_symmetry_topline_verdict"]
        == "symmetry contract topline | complete"
    )
    assert (
        summary["execution_meta_quick_status"]
        == "execution+meta quick | execution=complete | meta=complete"
    )
    assert (
        summary["execution_meta_integrated_quick_verdict"]
        == "execution+meta integrated | execution=complete | meta=complete"
    )
    assert (
        summary["execution_meta_topline_bundle"]
        == "execution+meta topline bundle | quick=execution+meta quick | execution=complete | meta=complete | integrated=execution+meta integrated | execution=complete | meta=complete"
    )
    assert (
        summary["execution_meta_bundle_ready_verdict"]
        == "execution+meta bundle ready | complete"
    )
    assert (
        summary["execution_meta_topline_ready"]
        == "execution+meta topline ready | complete"
    )
    assert (
        summary["execution_meta_stack_complete"]
        == "execution+meta stack complete | complete"
    )
    assert summary["execution_meta_contract_test_index_symmetry_fields"] == [
        "symmetry_regression_test",
        "execution_contract_symmetry_lock_included",
        "execution_contract_symmetry_regression_test",
        "execution_meta_contract_test_index_symmetry_fields",
    ]
    assert summary["contract_read_order_lock_included"] is True
    assert summary["reverse_screen_pointer_lock_included"] is True
    assert summary["reverse_screen_pointer_lock_scope"] == [
        "meta_contract_screen_summary"
    ]
    assert (
        summary["reverse_screen_pointer_scope_regression_test"]
        == "tests/unit/test_btc_1d_contract_read_order_runbook_contract.py"
    )
    assert (
        summary["contract_read_order_regression_test"]
        == "tests/unit/test_btc_1d_contract_read_order_runbook_contract.py"
    )
    assert summary["execution_meta_contract_test_index_md"].endswith(
        "btc_1d_execution_meta_contract_test_index_md_latest.md"
    )
    assert (
        summary["deprecated_aliases"]["all_health_standard_order_aligned"]
        == "Deprecated alias for health_order_aligned. Prefer health_order_aligned."
    )
    assert summary["health_standard_check_order_scope"] == [
        "practical_health",
        "research_stack_health",
        "contract_health",
    ]
    assert report["meta_contract_verdict"]["contract_is_fully_aligned"] is True
    assert "execution contract summary" in report["meta_contract_verdict"]["reason"]
    assert "execution contract entry scope" in report["meta_contract_verdict"]["reason"]
    assert "execution contract wording lock" in report["meta_contract_verdict"]["reason"]
    assert "meta_contract_topline_regression_test" in report["meta_contract_verdict"]["reason"]
    assert "execution contract symmetry key/set/map/bundle/ready/stack_complete/summary_ready metadata" in report["meta_contract_verdict"]["reason"]
    assert "execution_meta_stack_complete" in report["meta_contract_verdict"]["reason"]
    execution_entry = next(
        entry for entry in report["entries"] if entry["label"] == "execution_contract_screen"
    )
    assert (
        execution_entry["wording_regression_test"]
        == "tests/unit/test_btc_1d_execution_contract_wording_contract.py"
    )


def test_main_writes_latest_aliases(tmp_path: Path, monkeypatch) -> None:
    regression_lock = "tests/unit/test_btc_1d_operating_cli_help_contract.py"
    standard_order = ["practical", "research", "contract", "brief"]

    _write_json(
        tmp_path / "btc_1d_operating_brief_latest.json",
        {"regression_lock_test": regression_lock, "standard_check_order": standard_order},
    )
    _write_json(
        tmp_path / "btc_1d_operating_index_latest.json",
        {"regression_lock_test": regression_lock, "standard_check_order": standard_order},
    )
    _write_json(
        tmp_path / "btc_1d_quick_read_contract_screen_latest.json",
        {
            "report": {
                "regression_lock_test": regression_lock,
                "contract_summary": {"shared_standard_check_order": standard_order},
            }
        },
    )
    _write_json(
        tmp_path / "btc_1d_execution_contract_screen_latest.json",
        {
            "entries": [
                {
                    "label": "operating_brief",
                    "regression_lock_test": regression_lock,
                    "standard_check_order_reference": standard_order,
                },
                {
                    "label": "operating_index",
                    "regression_lock_test": regression_lock,
                    "standard_check_order_reference": standard_order,
                },
            ],
            "execution_contract_summary": {
                "regression_lock_test": regression_lock,
                "wording_regression_test": "tests/unit/test_btc_1d_execution_contract_wording_contract.py",
                "symmetry_regression_test": "tests/unit/test_btc_1d_execution_meta_summary_symmetry_contract.py",
                "standard_check_order_reference": standard_order,
                "execution_meta_quick_status": "execution+meta quick | execution=complete | meta=complete",
            },
        },
    )
    _write_json(
        tmp_path / "btc_1d_execution_meta_contract_test_index_latest.json",
        {
            "tests": [
                {
                    "label": "contract_read_order_runbook_contract",
                    "locks": [
                        "quick-read contract screen read order",
                        "execution contract screen read order",
                        "meta contract screen read order",
                        "execution meta contract test index read order",
                        "execution/meta contract test map reverse screen pointers",
                    ],
                }
            ],
            "summary": {
                "meta_contract_tests": [
                    "tests/unit/test_compare_btc_1d_meta_contract_screen.py",
                    "tests/unit/test_btc_1d_meta_contract_runbook_wording_contract.py",
                    "tests/unit/test_btc_1d_contract_read_order_runbook_contract.py",
                ]
            }
        },
    )
    _write_json(
        tmp_path / "btc_1d_practical_promotion_gate_latest.json",
        {
            "ok": True,
            "status_label": "btc_only_practical_with_caveats",
            "candidate": "candidate_a",
            "scope": "BTC-only",
            "caveats": [],
            "carry_metrics": {"sharpe": 1.0, "cagr": 0.3, "max_drawdown": 0.1},
        },
    )
    _write_json(
        tmp_path / "btc_1d_research_stack_operating_brief_latest.json",
        {
            "regression_lock_test": regression_lock,
            "standard_check_order_reference": standard_order,
            "quick_read_order_version": "research_stack_v2",
            "operating_brief": {
                "attack_frontier": "ratio112_tighter_stop_main",
                "attack_backup": "ratio111_tighter_stop_backup",
                "defensive_hold": "volatility_expansion_pullthrough_shorter_hold",
                "highest_priority_near_miss": "trend_dip_reversal_breakout_tighter_stop_mid_hold",
            },
            "models": {
                "attack_main": {"base_cagr": 0.4243, "base_mdd": 0.1609, "base_sharpe": 1.5613},
                "attack_backup": {"sensitivity_max_drift": 0.4172},
                "defensive_hold": {"status_label": "candidate_stage_hold"},
                "highest_priority_near_miss": {"candidate_stage_status": "validated_fail_hold"},
            },
        },
    )

    monkeypatch.setattr(meta_contract_screen, "ANALYSIS_DIR", tmp_path)

    assert meta_contract_screen.main() == 0

    latest_json = tmp_path / "btc_1d_meta_contract_screen_latest.json"
    latest_md = tmp_path / "btc_1d_meta_contract_screen_md_latest.md"
    assert latest_json.exists()
    assert latest_md.exists()

    latest_payload = json.loads(latest_json.read_text(encoding="utf-8"))
    assert latest_payload["meta_contract_summary"]["shared_regression_lock_test"] == regression_lock
    assert latest_payload["meta_contract_summary"]["shared_standard_check_order"] == standard_order
    assert "research_stack_operating_brief" in latest_payload["meta_contract_summary"]["standard_check_order_scope"]
    assert "execution_contract_screen" in latest_payload["meta_contract_summary"]["standard_check_order_scope"]
    assert "execution_contract_screen_operating_brief_entry" in latest_payload["meta_contract_summary"]["standard_check_order_scope"]
    assert "execution_contract_screen_operating_index_entry" in latest_payload["meta_contract_summary"]["standard_check_order_scope"]
    assert "practical_health" in latest_payload["meta_contract_summary"]["standard_check_order_scope"]
    assert "research_stack_health" in latest_payload["meta_contract_summary"]["standard_check_order_scope"]
    assert latest_payload["meta_contract_summary"]["health_order_aligned"] is True
    assert latest_payload["meta_contract_summary"]["all_health_standard_order_aligned"] is True
    assert latest_payload["meta_contract_summary"]["execution_contract_entry_scope_included"] is True
    assert latest_payload["meta_contract_summary"]["execution_contract_wording_lock_included"] is True
    assert latest_payload["meta_contract_summary"]["execution_contract_symmetry_lock_included"] is True
    assert (
        latest_payload["meta_contract_summary"]["meta_contract_topline_regression_test"]
        == "tests/unit/test_btc_1d_meta_contract_wording_contract.py"
    )
    assert latest_payload["meta_contract_summary"]["meta_contract_topline_reason_wording_included"] is True
    assert (
        latest_payload["meta_contract_summary"]["meta_contract_topline_status"]
        == "meta topline status | regression_test=tests/unit/test_btc_1d_meta_contract_wording_contract.py | reason_included=True"
    )
    assert (
        latest_payload["meta_contract_summary"]["meta_contract_topline_quick_status"]
        == "meta topline quick | lock=ok | reason=included"
    )
    assert (
        latest_payload["meta_contract_summary"]["meta_contract_topline_highlight"]
        == "topline highlight | lock=ok | reason=included"
    )
    assert (
        latest_payload["meta_contract_summary"]["meta_contract_reason_highlight_summary"]
        == "reason+highlight | summary_ready | reason=included"
    )
    assert (
        latest_payload["meta_contract_summary"]["meta_contract_reason_final_verdict"]
        == "reason final verdict | complete | reason=included"
    )
    assert (
        latest_payload["meta_contract_summary"]["meta_contract_integrated_topline_verdict"]
        == "meta contract integrated | topline=complete | reason=complete"
    )
    assert (
        latest_payload["meta_contract_summary"]["execution_contract_symmetry_regression_test"]
        == "tests/unit/test_btc_1d_execution_meta_summary_symmetry_contract.py"
    )
    assert latest_payload["meta_contract_summary"]["execution_contract_symmetry_fields"] == [
        "symmetry_regression_test",
        "execution_contract_symmetry_lock_included",
        "execution_contract_symmetry_regression_test",
        "execution_meta_contract_test_index_symmetry_fields",
    ]
    assert latest_payload["meta_contract_summary"]["execution_contract_symmetry_field_set"] == [
        "symmetry_regression_test",
        "execution_contract_symmetry_lock_included",
        "execution_contract_symmetry_regression_test",
        "execution_meta_contract_test_index_symmetry_fields",
    ]
    assert (
        latest_payload["meta_contract_summary"]["execution_contract_symmetry_field_map"]
        == "symmetry field map | symmetry_regression_test | execution_contract_symmetry_lock_included | execution_contract_symmetry_regression_test | execution_meta_contract_test_index_symmetry_fields"
    )
    assert (
        latest_payload["meta_contract_summary"]["execution_contract_symmetry_contract_bundle"]
        == "symmetry contract bundle | symmetry_regression_test | execution_contract_symmetry_lock_included | execution_contract_symmetry_regression_test | execution_meta_contract_test_index_symmetry_fields"
    )
    assert latest_payload["meta_contract_summary"]["execution_contract_symmetry_ready"] is True
    assert (
        latest_payload["meta_contract_summary"]["execution_contract_symmetry_reason_scope"]
        == "symmetry reason scope | key | set | map | bundle | ready"
    )
    assert (
        latest_payload["meta_contract_summary"]["execution_contract_symmetry_reason_range_summary"]
        == "symmetry reason range | key | set | map | bundle | ready | stack_complete"
    )
    assert (
        latest_payload["meta_contract_summary"]["execution_contract_symmetry_reason_final_summary"]
        == "symmetry reason final | key | set | map | bundle | ready | stack_complete | summary_ready"
    )
    assert (
        latest_payload["meta_contract_summary"]["execution_contract_symmetry_status"]
        == "symmetry contract status | ready=True | symmetry reason scope | key | set | map | bundle | ready"
    )
    assert latest_payload["meta_contract_summary"]["execution_contract_symmetry_stack_complete"] is True
    assert latest_payload["meta_contract_summary"]["execution_contract_symmetry_summary_ready"] is True
    assert (
        latest_payload["meta_contract_summary"]["execution_contract_symmetry_topline_verdict"]
        == "symmetry contract topline | complete"
    )
    assert (
        latest_payload["meta_contract_summary"]["execution_meta_quick_status"]
        == "execution+meta quick | execution=complete | meta=complete"
    )
    assert (
        latest_payload["meta_contract_summary"]["execution_meta_integrated_quick_verdict"]
        == "execution+meta integrated | execution=complete | meta=complete"
    )
    assert (
        latest_payload["meta_contract_summary"]["execution_meta_topline_bundle"]
        == "execution+meta topline bundle | quick=execution+meta quick | execution=complete | meta=complete | integrated=execution+meta integrated | execution=complete | meta=complete"
    )
    assert (
        latest_payload["meta_contract_summary"]["execution_meta_bundle_ready_verdict"]
        == "execution+meta bundle ready | complete"
    )
    assert (
        latest_payload["meta_contract_summary"]["execution_meta_topline_ready"]
        == "execution+meta topline ready | complete"
    )
    assert (
        latest_payload["meta_contract_summary"]["execution_meta_stack_complete"]
        == "execution+meta stack complete | complete"
    )
    assert latest_payload["meta_contract_summary"]["execution_meta_contract_test_index_symmetry_fields"] == [
        "symmetry_regression_test",
        "execution_contract_symmetry_lock_included",
        "execution_contract_symmetry_regression_test",
        "execution_meta_contract_test_index_symmetry_fields",
    ]
    assert latest_payload["meta_contract_summary"]["contract_read_order_lock_included"] is True
    assert latest_payload["meta_contract_summary"]["reverse_screen_pointer_lock_included"] is True
    assert latest_payload["meta_contract_summary"]["reverse_screen_pointer_lock_scope"] == [
        "meta_contract_screen_summary"
    ]
    assert (
        latest_payload["meta_contract_summary"]["reverse_screen_pointer_scope_regression_test"]
        == "tests/unit/test_btc_1d_contract_read_order_runbook_contract.py"
    )
    assert (
        latest_payload["meta_contract_summary"]["contract_read_order_regression_test"]
        == "tests/unit/test_btc_1d_contract_read_order_runbook_contract.py"
    )
    assert latest_payload["meta_contract_summary"]["execution_meta_contract_test_index_md"].endswith(
        "btc_1d_execution_meta_contract_test_index_md_latest.md"
    )
    assert "execution contract symmetry key/set/map/bundle/ready/stack_complete/summary_ready metadata" in latest_payload["meta_contract_verdict"]["reason"]
    assert (
        latest_payload["meta_contract_summary"]["deprecated_aliases"]["all_health_standard_order_aligned"]
        == "Deprecated alias for health_order_aligned. Prefer health_order_aligned."
    )
    assert "practical_health" in latest_payload["meta_contract_summary"]["health_standard_check_order_scope"]
    assert "research_stack_health" in latest_payload["meta_contract_summary"]["health_standard_check_order_scope"]
    assert "contract_health" in latest_payload["meta_contract_summary"]["health_standard_check_order_scope"]
    assert "execution contract summary" in latest_payload["meta_contract_verdict"]["reason"]
    assert "execution contract entry scope" in latest_payload["meta_contract_verdict"]["reason"]
    assert "execution contract wording lock" in latest_payload["meta_contract_verdict"]["reason"]
    assert "meta_contract_topline_regression_test" in latest_payload["meta_contract_verdict"]["reason"]
    assert "execution_meta_stack_complete" in latest_payload["meta_contract_verdict"]["reason"]
    assert "BTC 1d Meta Contract Screen" in latest_md.read_text(encoding="utf-8")
    assert "Meta contract integrated topline verdict: `meta contract integrated | topline=complete | reason=complete`" in latest_md.read_text(encoding="utf-8")
    assert "Execution meta integrated quick verdict: `execution+meta integrated | execution=complete | meta=complete`" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "Execution meta topline bundle: `execution+meta topline bundle | quick=execution+meta quick | execution=complete | meta=complete | integrated=execution+meta integrated | execution=complete | meta=complete`" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "Execution meta bundle ready verdict: `execution+meta bundle ready | complete`" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "Execution meta topline ready: `execution+meta topline ready | complete`" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "Execution meta stack complete: `execution+meta stack complete | complete`" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "Execution contract symmetry topline verdict: `symmetry contract topline | complete`" in latest_md.read_text(encoding="utf-8")
    assert "Execution contract entry scope included: `True`" in latest_md.read_text(encoding="utf-8")
    assert "Execution contract wording lock included: `True`" in latest_md.read_text(encoding="utf-8")
    assert "Execution contract symmetry lock included: `True`" in latest_md.read_text(encoding="utf-8")
    assert "Meta contract topline regression lock: `tests/unit/test_btc_1d_meta_contract_wording_contract.py`" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "Meta contract topline reason wording included: `True`" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "Meta contract topline status: `meta topline status | regression_test=tests/unit/test_btc_1d_meta_contract_wording_contract.py | reason_included=True`" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "Meta contract topline quick status: `meta topline quick | lock=ok | reason=included`" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "Topline quick highlight: `topline highlight | lock=ok | reason=included`" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "Reason highlight summary: `reason+highlight | summary_ready | reason=included`" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "Reason final verdict: `reason final verdict | complete | reason=included`" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "Execution contract symmetry ready: `True`" in latest_md.read_text(encoding="utf-8")
    assert "Execution contract symmetry reason scope: `symmetry reason scope | key | set | map | bundle | ready`" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "Execution contract symmetry reason range summary: `symmetry reason range | key | set | map | bundle | ready | stack_complete`" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "Execution contract symmetry reason final summary: `symmetry reason final | key | set | map | bundle | ready | stack_complete | summary_ready`" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "Execution contract symmetry status: `symmetry contract status | ready=True | symmetry reason scope | key | set | map | bundle | ready`" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "Execution contract symmetry stack complete: `True`" in latest_md.read_text(encoding="utf-8")
    assert "Execution contract symmetry summary ready: `True`" in latest_md.read_text(encoding="utf-8")
    assert "Execution meta quick status: `execution+meta quick | execution=complete | meta=complete`" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "Contract read-order lock included: `True`" in latest_md.read_text(encoding="utf-8")
    assert "Contract read-order regression lock: `tests/unit/test_btc_1d_contract_read_order_runbook_contract.py`" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "Reverse screen pointer lock included: `True`" in latest_md.read_text(encoding="utf-8")
    assert "Reverse screen pointer lock scope: `['meta_contract_screen_summary']`" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "Reverse screen pointer scope regression lock: `tests/unit/test_btc_1d_contract_read_order_runbook_contract.py`" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "Execution meta contract test index: `" in latest_md.read_text(encoding="utf-8")
    assert "btc_1d_execution_meta_contract_test_index_md_latest.md`" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "Execution-meta reason field-set lock: `execution_meta_quick_status/.../execution_meta_stack_complete field-set reason wording`" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "Execution-meta reason final-sentence lock: `execution_meta_quick_status/.../execution_meta_stack_complete final sentence wording`" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "Wording regression lock: `tests/unit/test_btc_1d_execution_contract_wording_contract.py`" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "Deprecated alias: `all_health_standard_order_aligned` -> `health_order_aligned`" in latest_md.read_text(
        encoding="utf-8"
    )
