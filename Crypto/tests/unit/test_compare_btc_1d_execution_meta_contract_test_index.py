from __future__ import annotations

import json
from pathlib import Path

from scripts import compare_btc_1d_execution_meta_contract_test_index as test_index


def test_build_report_indexes_execution_and_meta_contract_tests() -> None:
    report = test_index.build_report()

    assert report["summary"]["execution_meta_contract_test_index_ready"] is True
    assert report["summary"]["test_count"] == len(report["tests"])
    assert (
        report["summary"]["screen_pointers"]["quick_read_contract_screen_md"]
        == "analysis_results\\btc_1d_quick_read_contract_screen_md_latest.md"
    )
    assert (
        report["summary"]["screen_pointers"]["execution_contract_screen_md"]
        == "analysis_results\\btc_1d_execution_contract_screen_md_latest.md"
    )
    assert (
        report["summary"]["screen_pointers"]["meta_contract_screen_md"]
        == "analysis_results\\btc_1d_meta_contract_screen_md_latest.md"
    )
    assert "tests/unit/test_compare_btc_1d_meta_contract_screen.py" in report["summary"]["meta_contract_tests"]
    assert "tests/unit/test_btc_1d_meta_contract_wording_contract.py" in report["summary"]["meta_contract_tests"]
    assert "tests/unit/test_btc_1d_contract_read_order_runbook_contract.py" in report["summary"]["meta_contract_tests"]
    assert "tests/unit/test_compare_btc_1d_execution_contract_screen.py" in report["summary"]["execution_contract_tests"]
    assert "tests/unit/test_btc_1d_execution_contract_wording_contract.py" in report["summary"]["execution_contract_tests"]
    assert "tests/unit/test_btc_1d_execution_meta_summary_symmetry_contract.py" in report["summary"]["execution_contract_tests"]
    execution_screen = next(
        item for item in report["tests"] if item["label"] == "execution_contract_screen"
    )
    assert "wording_regression_test metadata" in execution_screen["locks"]
    meta_runbook_wording = next(
        item for item in report["tests"] if item["label"] == "meta_contract_runbook_wording_contract"
    )
    assert "execution_meta_quick_status/.../execution_meta_stack_complete field-set reason wording" in meta_runbook_wording["locks"]
    assert "execution_meta_quick_status/.../execution_meta_stack_complete final sentence wording" in meta_runbook_wording["locks"]
    assert "execution_meta_quick_status runbook field wording" in meta_runbook_wording["locks"]
    assert "meta_contract_topline_regression_test reason wording" in meta_runbook_wording["locks"]
    assert "meta_contract_topline_reason_wording_included runbook field wording" in meta_runbook_wording["locks"]
    assert "meta_contract_topline_status runbook field wording" in meta_runbook_wording["locks"]
    assert "meta_contract_topline_quick_status runbook field wording" in meta_runbook_wording["locks"]
    assert "meta_contract_topline_highlight runbook field wording" in meta_runbook_wording["locks"]
    assert "meta_contract_reason_highlight_summary runbook field wording" in meta_runbook_wording["locks"]
    assert "meta_contract_reason_final_verdict runbook field wording" in meta_runbook_wording["locks"]
    assert "meta_contract_integrated_topline_verdict runbook field wording" in meta_runbook_wording["locks"]
    assert "execution_meta_integrated_quick_verdict runbook field wording" in meta_runbook_wording["locks"]
    assert "execution_meta_topline_bundle runbook field wording" in meta_runbook_wording["locks"]
    assert "execution_meta_bundle_ready_verdict runbook field wording" in meta_runbook_wording["locks"]
    assert "execution_meta_topline_ready runbook field wording" in meta_runbook_wording["locks"]
    assert "execution_meta_stack_complete runbook field wording" in meta_runbook_wording["locks"]
    symmetry = next(
        item for item in report["tests"] if item["label"] == "execution_meta_summary_symmetry_contract"
    )
    assert "execution/meta summary reverse-pointer wording symmetry" in symmetry["locks"]
    assert "symmetry_regression_test runbook field wording" in symmetry["locks"]
    assert "execution_contract_symmetry_lock_included runbook field wording" in symmetry["locks"]
    assert "symmetry_fields cross-surface wording" in symmetry["locks"]
    assert "execution_contract_symmetry_regression_test cross-surface wording" in symmetry["locks"]
    assert "execution_contract_symmetry_fields cross-surface wording" in symmetry["locks"]
    assert "execution_meta_contract_test_index_symmetry_fields cross-surface wording" in symmetry["locks"]
    assert "symmetry_field_set cross-surface wording" in symmetry["locks"]
    assert "execution_contract_symmetry_field_set cross-surface wording" in symmetry["locks"]
    assert "symmetry_field_map cross-surface wording" in symmetry["locks"]
    assert "execution_contract_symmetry_field_map cross-surface wording" in symmetry["locks"]
    assert "symmetry_contract_bundle cross-surface wording" in symmetry["locks"]
    assert "execution_contract_symmetry_contract_bundle cross-surface wording" in symmetry["locks"]
    assert "symmetry_contract_ready cross-surface wording" in symmetry["locks"]
    assert "execution_contract_symmetry_ready cross-surface wording" in symmetry["locks"]
    assert "execution contract symmetry key/set/map/bundle/ready/stack_complete/summary_ready metadata reason wording" in symmetry["locks"]
    assert "symmetry_reason_scope cross-surface wording" in symmetry["locks"]
    assert "symmetry_reason_range_summary cross-surface wording" in symmetry["locks"]
    assert "symmetry_reason_final_summary cross-surface wording" in symmetry["locks"]
    assert "execution_contract_symmetry_reason_scope cross-surface wording" in symmetry["locks"]
    assert "execution_contract_symmetry_reason_range_summary cross-surface wording" in symmetry["locks"]
    assert "execution_contract_symmetry_reason_final_summary cross-surface wording" in symmetry["locks"]
    assert "symmetry_contract_status cross-surface wording" in symmetry["locks"]
    assert "execution_contract_symmetry_status cross-surface wording" in symmetry["locks"]
    assert "symmetry_contract_stack_complete cross-surface wording" in symmetry["locks"]
    assert "execution_contract_symmetry_stack_complete cross-surface wording" in symmetry["locks"]
    assert "symmetry_contract_summary_ready cross-surface wording" in symmetry["locks"]
    assert "execution_contract_symmetry_summary_ready cross-surface wording" in symmetry["locks"]
    assert "reverse_screen_pointer_lock_included cross-surface wording" in symmetry["locks"]
    assert "reverse_screen_pointer_lock_scope cross-surface wording" in symmetry["locks"]
    assert "reverse_screen_pointer_scope_regression_test cross-surface wording" in symmetry["locks"]
    assert "execution_contract_screen_summary" in symmetry["scope"]
    assert "meta_contract_screen_summary" in symmetry["scope"]
    assert "operator_runbook" in symmetry["scope"]
    assert "shadow_update_runbook" in symmetry["scope"]
    read_order = next(
        item for item in report["tests"] if item["label"] == "contract_read_order_runbook_contract"
    )
    assert "execution meta contract test index read order" in read_order["locks"]
    assert "execution/meta contract test map reverse screen pointers" in read_order["locks"]
    assert "reverse_screen_pointer_lock_included runbook field wording" in read_order["locks"]
    assert "reverse_screen_pointer_lock_scope runbook field wording" in read_order["locks"]
    assert "reverse_screen_pointer_scope_regression_test runbook field wording" in read_order["locks"]
    assert "execution_contract_screen_summary" in read_order["scope"]
    assert "meta_contract_screen_summary" in read_order["scope"]
    execution_wording = next(
        item for item in report["tests"] if item["label"] == "execution_contract_wording_contract"
    )
    meta_wording = next(
        item for item in report["tests"] if item["label"] == "meta_contract_wording_contract"
    )
    assert "execution_meta_quick_status/.../execution_meta_stack_complete field-set reason wording" in meta_wording["locks"]
    assert "execution_meta_quick_status/.../execution_meta_stack_complete final sentence wording" in meta_wording["locks"]
    assert "execution_meta_quick_status screen summary metadata" in meta_wording["locks"]
    assert "meta_contract_topline_regression_test screen summary metadata" in meta_wording["locks"]
    assert "meta_contract_topline_status screen summary metadata" in meta_wording["locks"]
    assert "meta_contract_topline_quick_status screen summary metadata" in meta_wording["locks"]
    assert "meta_contract_topline_highlight screen summary metadata" in meta_wording["locks"]
    assert "meta_contract_reason_highlight_summary screen summary metadata" in meta_wording["locks"]
    assert "meta_contract_reason_final_verdict screen summary metadata" in meta_wording["locks"]
    assert "meta_contract_integrated_topline_verdict screen summary metadata" in meta_wording["locks"]
    assert "execution_meta_integrated_quick_verdict screen summary metadata" in meta_wording["locks"]
    assert "execution_meta_topline_bundle screen summary metadata" in meta_wording["locks"]
    assert "execution_meta_bundle_ready_verdict screen summary metadata" in meta_wording["locks"]
    assert "execution_meta_topline_ready screen summary metadata" in meta_wording["locks"]
    assert "execution_meta_stack_complete screen summary metadata" in meta_wording["locks"]
    assert "execution contract symmetry topline verdict wording" in meta_wording["locks"]
    assert "execution contract symmetry ready wording" in meta_wording["locks"]
    assert "execution contract symmetry summary ready wording" in meta_wording["locks"]
    assert "contract fully aligned wording" in meta_wording["locks"]
    assert "execution_meta_quick_status/.../execution_meta_stack_complete field-set reason wording" in execution_wording["locks"]
    assert "execution_meta_quick_status/.../execution_meta_stack_complete final sentence wording" in execution_wording["locks"]
    assert "symmetry contract topline verdict wording" in execution_wording["locks"]
    assert "meta_contract_integrated_topline_verdict execution-summary wording" in execution_wording["locks"]
    assert "execution_meta_quick_status execution-summary wording" in execution_wording["locks"]
    assert "execution_meta_integrated_quick_verdict execution-summary wording" in execution_wording["locks"]
    assert "execution_meta_topline_bundle execution-summary wording" in execution_wording["locks"]
    assert "execution_meta_bundle_ready_verdict execution-summary wording" in execution_wording["locks"]
    assert "execution_meta_topline_ready execution-summary wording" in execution_wording["locks"]
    assert "execution_meta_stack_complete execution-summary wording" in execution_wording["locks"]
    assert "symmetry_contract_topline_verdict cross-surface wording" in symmetry["locks"]
    assert "execution_contract_symmetry_topline_verdict cross-surface wording" in symmetry["locks"]


def test_main_writes_latest_aliases(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(test_index, "ANALYSIS_DIR", tmp_path)

    assert test_index.main() == 0

    latest_json = tmp_path / "btc_1d_execution_meta_contract_test_index_latest.json"
    latest_md = tmp_path / "btc_1d_execution_meta_contract_test_index_md_latest.md"
    assert latest_json.exists()
    assert latest_md.exists()

    payload = json.loads(latest_json.read_text(encoding="utf-8"))
    assert payload["summary"]["execution_meta_contract_test_index_ready"] is True
    assert "Execution contract tests:" in latest_md.read_text(encoding="utf-8")
    assert "Quick-read contract screen:" in latest_md.read_text(encoding="utf-8")
    assert "Execution contract screen:" in latest_md.read_text(encoding="utf-8")
    assert "Meta contract screen:" in latest_md.read_text(encoding="utf-8")
    assert "execution/meta contract test map reverse screen pointers" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "reverse_screen_pointer_lock_included runbook field wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "reverse_screen_pointer_lock_scope runbook field wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "reverse_screen_pointer_scope_regression_test runbook field wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "## execution_contract_wording_contract" in latest_md.read_text(encoding="utf-8")
    assert "## meta_contract_wording_contract" in latest_md.read_text(encoding="utf-8")
    assert "## execution_meta_summary_symmetry_contract" in latest_md.read_text(encoding="utf-8")
    assert "execution/meta summary reverse-pointer wording symmetry" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "symmetry_regression_test runbook field wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "meta_contract_topline_regression_test reason wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution_meta_quick_status/.../execution_meta_stack_complete field-set reason wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution_meta_quick_status/.../execution_meta_stack_complete final sentence wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution_meta_quick_status runbook field wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "meta_contract_topline_reason_wording_included runbook field wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "meta_contract_topline_status runbook field wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "meta_contract_topline_quick_status runbook field wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "meta_contract_topline_highlight runbook field wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "meta_contract_reason_highlight_summary runbook field wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "meta_contract_reason_final_verdict runbook field wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "meta_contract_integrated_topline_verdict runbook field wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution_meta_integrated_quick_verdict runbook field wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution_meta_topline_bundle runbook field wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution_meta_bundle_ready_verdict runbook field wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution_meta_topline_ready runbook field wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution_meta_stack_complete runbook field wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "meta_contract_integrated_topline_verdict execution-summary wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution_meta_quick_status execution-summary wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution_meta_integrated_quick_verdict execution-summary wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution_meta_topline_bundle execution-summary wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution_meta_bundle_ready_verdict execution-summary wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution_meta_topline_ready execution-summary wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution_meta_stack_complete execution-summary wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution_contract_symmetry_lock_included runbook field wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "symmetry_fields cross-surface wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution_contract_symmetry_regression_test cross-surface wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution_contract_symmetry_fields cross-surface wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution_meta_contract_test_index_symmetry_fields cross-surface wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "symmetry_field_set cross-surface wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution_contract_symmetry_field_set cross-surface wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "symmetry_field_map cross-surface wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution_contract_symmetry_field_map cross-surface wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "symmetry_contract_bundle cross-surface wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution_contract_symmetry_contract_bundle cross-surface wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "symmetry_contract_ready cross-surface wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution_contract_symmetry_ready cross-surface wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution contract symmetry key/set/map/bundle/ready/stack_complete/summary_ready metadata reason wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "symmetry_reason_scope cross-surface wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "symmetry_reason_range_summary cross-surface wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "symmetry_reason_final_summary cross-surface wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution_contract_symmetry_reason_scope cross-surface wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution_contract_symmetry_reason_range_summary cross-surface wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution_contract_symmetry_reason_final_summary cross-surface wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "symmetry_contract_status cross-surface wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution_contract_symmetry_status cross-surface wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "symmetry_contract_stack_complete cross-surface wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution_contract_symmetry_stack_complete cross-surface wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "symmetry_contract_summary_ready cross-surface wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution_contract_symmetry_summary_ready cross-surface wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "symmetry contract topline verdict wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "symmetry_contract_topline_verdict cross-surface wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution_contract_symmetry_topline_verdict cross-surface wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution contract symmetry topline verdict wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "meta_contract_topline_regression_test screen summary metadata" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution_meta_quick_status screen summary metadata" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "meta_contract_topline_status screen summary metadata" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "meta_contract_topline_quick_status screen summary metadata" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "meta_contract_topline_highlight screen summary metadata" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "meta_contract_reason_highlight_summary screen summary metadata" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "meta_contract_reason_final_verdict screen summary metadata" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "meta_contract_integrated_topline_verdict screen summary metadata" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution_meta_integrated_quick_verdict screen summary metadata" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution_meta_topline_bundle screen summary metadata" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution_meta_bundle_ready_verdict screen summary metadata" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution_meta_topline_ready screen summary metadata" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution_meta_stack_complete screen summary metadata" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution contract symmetry ready wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "execution contract symmetry summary ready wording" in latest_md.read_text(
        encoding="utf-8"
    )
    assert "contract fully aligned wording" in latest_md.read_text(
        encoding="utf-8"
    )
