from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


ANALYSIS_DIR = Path("analysis_results")


def build_report() -> dict:
    screen_pointers = {
        "quick_read_contract_screen_md": str(
            ANALYSIS_DIR / "btc_1d_quick_read_contract_screen_md_latest.md"
        ),
        "execution_contract_screen_md": str(
            ANALYSIS_DIR / "btc_1d_execution_contract_screen_md_latest.md"
        ),
        "meta_contract_screen_md": str(
            ANALYSIS_DIR / "btc_1d_meta_contract_screen_md_latest.md"
        ),
    }
    tests = [
        {
            "label": "operating_cli_help_contract",
            "path": "tests/unit/test_btc_1d_operating_cli_help_contract.py",
            "locks": [
                "Standard operating check order help wording",
            ],
            "scope": ["practical", "research", "contract", "brief"],
            "track": "shared_contract",
        },
        {
            "label": "contract_alias_wording_contract",
            "path": "tests/unit/test_btc_1d_contract_alias_wording_contract.py",
            "locks": [
                "health_order_aligned deprecated alias wording",
            ],
            "scope": ["contract_health", "meta_contract_screen"],
            "track": "shared_contract",
        },
        {
            "label": "contract_docs_contract",
            "path": "tests/unit/test_btc_1d_contract_docs_contract.py",
            "locks": [
                "operating order help wording",
                "alias migration help wording",
            ],
            "scope": ["runbook", "help"],
            "track": "shared_contract",
        },
        {
            "label": "meta_contract_screen",
            "path": "tests/unit/test_compare_btc_1d_meta_contract_screen.py",
            "locks": [
                "meta contract verdict reason wording",
                "execution_meta_quick_status/.../execution_meta_stack_complete field-set reason wording",
                "execution_meta_quick_status/.../execution_meta_stack_complete final sentence wording",
                "execution contract summary inclusion",
                "execution contract entry scope inclusion",
                "execution contract wording lock inclusion",
            ],
            "scope": ["meta_contract_screen"],
            "track": "meta_contract",
        },
        {
            "label": "meta_contract_runbook_wording_contract",
            "path": "tests/unit/test_btc_1d_meta_contract_runbook_wording_contract.py",
            "locks": [
                "runbook wording for latest meta-contract reason scope",
                "execution_meta_quick_status/.../execution_meta_stack_complete field-set reason wording",
                "execution_meta_quick_status/.../execution_meta_stack_complete final sentence wording",
                "execution_meta_quick_status runbook field wording",
                "meta_contract_topline_regression_test reason wording",
                "meta_contract_topline_reason_wording_included runbook field wording",
                "meta_contract_topline_status runbook field wording",
                "meta_contract_topline_quick_status runbook field wording",
                "meta_contract_topline_highlight runbook field wording",
                "meta_contract_reason_highlight_summary runbook field wording",
                "meta_contract_reason_final_verdict runbook field wording",
                "meta_contract_integrated_topline_verdict runbook field wording",
                "execution_meta_integrated_quick_verdict runbook field wording",
                "execution_meta_topline_bundle runbook field wording",
                "execution_meta_bundle_ready_verdict runbook field wording",
                "execution_meta_topline_ready runbook field wording",
                "execution_meta_stack_complete runbook field wording",
            ],
            "scope": ["operator_runbook", "shadow_update_runbook"],
            "track": "meta_contract",
        },
        {
            "label": "meta_contract_wording_contract",
            "path": "tests/unit/test_btc_1d_meta_contract_wording_contract.py",
            "locks": [
                "execution_meta_quick_status/.../execution_meta_stack_complete field-set reason wording",
                "execution_meta_quick_status/.../execution_meta_stack_complete final sentence wording",
                "execution_meta_quick_status screen summary metadata",
                "meta_contract_topline_regression_test screen summary metadata",
                "meta_contract_topline_status screen summary metadata",
                "meta_contract_topline_quick_status screen summary metadata",
                "meta_contract_topline_highlight screen summary metadata",
                "meta_contract_reason_highlight_summary screen summary metadata",
                "meta_contract_reason_final_verdict screen summary metadata",
                "meta_contract_integrated_topline_verdict screen summary metadata",
                "execution_meta_integrated_quick_verdict screen summary metadata",
                "execution_meta_topline_bundle screen summary metadata",
                "execution_meta_bundle_ready_verdict screen summary metadata",
                "execution_meta_topline_ready screen summary metadata",
                "execution_meta_stack_complete screen summary metadata",
                "execution contract symmetry topline verdict wording",
                "execution contract symmetry ready wording",
                "execution contract symmetry summary ready wording",
                "contract fully aligned wording",
            ],
            "scope": ["meta_contract_screen"],
            "track": "meta_contract",
        },
        {
            "label": "contract_read_order_runbook_contract",
            "path": "tests/unit/test_btc_1d_contract_read_order_runbook_contract.py",
            "locks": [
                "quick-read contract screen read order",
                "execution contract screen read order",
                "meta contract screen read order",
                "execution meta contract test index read order",
                "execution/meta contract test map reverse screen pointers",
                "reverse_screen_pointer_lock_included runbook field wording",
                "reverse_screen_pointer_lock_scope runbook field wording",
                "reverse_screen_pointer_scope_regression_test runbook field wording",
            ],
            "scope": [
                "operator_runbook",
                "shadow_update_runbook",
                "quick_read_contract_flow",
                "execution_contract_screen_summary",
                "meta_contract_screen_summary",
            ],
            "track": "meta_contract",
        },
        {
            "label": "execution_contract_screen",
            "path": "tests/unit/test_compare_btc_1d_execution_contract_screen.py",
            "locks": [
                "execution contract screen summary fields",
                "entry-level regression lock metadata",
                "entry-level standard check order metadata",
                "wording_regression_test metadata",
            ],
            "scope": ["execution_contract_screen"],
            "track": "execution_contract",
        },
        {
            "label": "execution_contract_wording_contract",
            "path": "tests/unit/test_btc_1d_execution_contract_wording_contract.py",
            "locks": [
                "execution contract health wording",
                "execution contract read wording",
                "execution contract reason wording",
                "execution_meta_quick_status/.../execution_meta_stack_complete field-set reason wording",
                "execution_meta_quick_status/.../execution_meta_stack_complete final sentence wording",
                "symmetry contract topline verdict wording",
                "meta_contract_integrated_topline_verdict execution-summary wording",
                "execution_meta_quick_status execution-summary wording",
                "execution_meta_integrated_quick_verdict execution-summary wording",
                "execution_meta_topline_bundle execution-summary wording",
                "execution_meta_bundle_ready_verdict execution-summary wording",
                "execution_meta_topline_ready execution-summary wording",
                "execution_meta_stack_complete execution-summary wording",
            ],
            "scope": ["execution_contract_screen", "runbook"],
            "track": "execution_contract",
        },
        {
            "label": "execution_meta_summary_symmetry_contract",
            "path": "tests/unit/test_btc_1d_execution_meta_summary_symmetry_contract.py",
            "locks": [
                "execution/meta summary reverse-pointer wording symmetry",
                "symmetry_regression_test runbook field wording",
                "execution_contract_symmetry_lock_included runbook field wording",
                "symmetry_fields cross-surface wording",
                "execution_contract_symmetry_regression_test cross-surface wording",
                "execution_contract_symmetry_fields cross-surface wording",
                "execution_meta_contract_test_index_symmetry_fields cross-surface wording",
                "symmetry_field_set cross-surface wording",
                "execution_contract_symmetry_field_set cross-surface wording",
                "symmetry_field_map cross-surface wording",
                "execution_contract_symmetry_field_map cross-surface wording",
                "symmetry_contract_bundle cross-surface wording",
                "execution_contract_symmetry_contract_bundle cross-surface wording",
                "symmetry_contract_ready cross-surface wording",
                "execution_contract_symmetry_ready cross-surface wording",
                "execution contract symmetry key/set/map/bundle/ready/stack_complete/summary_ready metadata reason wording",
                "symmetry_reason_scope cross-surface wording",
                "symmetry_reason_range_summary cross-surface wording",
                "symmetry_reason_final_summary cross-surface wording",
                "execution_contract_symmetry_reason_scope cross-surface wording",
                "execution_contract_symmetry_reason_range_summary cross-surface wording",
                "execution_contract_symmetry_reason_final_summary cross-surface wording",
                "symmetry_contract_status cross-surface wording",
                "execution_contract_symmetry_status cross-surface wording",
                "symmetry_contract_stack_complete cross-surface wording",
                "execution_contract_symmetry_stack_complete cross-surface wording",
                "symmetry_contract_summary_ready cross-surface wording",
                "execution_contract_symmetry_summary_ready cross-surface wording",
                "symmetry_contract_topline_verdict cross-surface wording",
                "execution_contract_symmetry_topline_verdict cross-surface wording",
                "reverse_screen_pointer_lock_included cross-surface wording",
                "reverse_screen_pointer_lock_scope cross-surface wording",
                "reverse_screen_pointer_scope_regression_test cross-surface wording",
            ],
            "scope": [
                "execution_contract_screen_summary",
                "meta_contract_screen_summary",
                "operator_runbook",
                "shadow_update_runbook",
            ],
            "track": "execution_contract",
        },
    ]

    summary = {
        "shared_contract_tests": [t["path"] for t in tests if t["track"] == "shared_contract"],
        "meta_contract_tests": [t["path"] for t in tests if t["track"] == "meta_contract"],
        "execution_contract_tests": [t["path"] for t in tests if t["track"] == "execution_contract"],
        "test_count": len(tests),
        "execution_meta_contract_test_index_ready": True,
        "screen_pointers": screen_pointers,
    }

    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "summary": summary,
        "tests": tests,
    }


def _render_markdown(report: dict) -> str:
    summary = report["summary"]
    lines = [
        "# BTC 1d Execution Meta Contract Test Index",
        "",
        f"- Test count: `{summary['test_count']}`",
        f"- Execution meta contract test index ready: `{summary['execution_meta_contract_test_index_ready']}`",
        f"- Shared contract tests: `{summary['shared_contract_tests']}`",
        f"- Meta contract tests: `{summary['meta_contract_tests']}`",
        f"- Execution contract tests: `{summary['execution_contract_tests']}`",
        f"- Quick-read contract screen: `{summary['screen_pointers']['quick_read_contract_screen_md']}`",
        f"- Execution contract screen: `{summary['screen_pointers']['execution_contract_screen_md']}`",
        f"- Meta contract screen: `{summary['screen_pointers']['meta_contract_screen_md']}`",
        "",
    ]
    for test in report["tests"]:
        lines.extend(
            [
                f"## {test['label']}",
                f"- path: `{test['path']}`",
                f"- track: `{test['track']}`",
                f"- scope: `{test['scope']}`",
                "- locks:",
            ]
        )
        lines.extend([f"  - {lock}" for lock in test["locks"]])
        lines.append("")
    return "\n".join(lines)


def _write_latest_aliases(json_path: Path, md_path: Path) -> dict:
    latest_json = json_path.with_name("btc_1d_execution_meta_contract_test_index_latest.json")
    latest_md = md_path.with_name("btc_1d_execution_meta_contract_test_index_md_latest.md")
    latest_json.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
    latest_md.write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")
    return {
        "btc_1d_execution_meta_contract_test_index": str(latest_json),
        "btc_1d_execution_meta_contract_test_index_md": str(latest_md),
    }


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_execution_meta_contract_test_index_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_execution_meta_contract_test_index_{stamp}.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    latest_aliases = _write_latest_aliases(json_path, md_path)
    print(
        json.dumps(
            {
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "latest_aliases": latest_aliases,
                "report": report,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
