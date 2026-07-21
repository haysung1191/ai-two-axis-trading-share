from __future__ import annotations

import json
from pathlib import Path

from scripts.compare_btc_1d_quick_read_contract_screen import _render_markdown, _write_latest_aliases, build_report


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_build_report_reads_latest_contract_versions(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir / "btc_1d_operating_brief_latest.json",
        {
            "quick_read_order_version": "operating_v3",
            "standard_check_order": ["practical", "research", "contract", "brief"],
            "quick_read_order": [
                "practical_status",
                "combined_health",
                "research_stack_status",
                "carry",
                "quick_read_contract",
                "open_first",
            ],
            "paper_execution_contract_checked": True,
            "paper_execution_contract_aligned": True,
            "contract_health_operating_contract_aligned": True,
            "contract_health_paper_execution_contract_aligned": True,
            "contract_health_contracts_are_well_partitioned": True,
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_index_latest.json",
        {
            "quick_read_order_version": "operating_v3",
            "standard_check_order": ["practical", "research", "contract", "brief"],
            "quick_read_order": [
                "practical_status",
                "combined_health",
                "research_stack_status",
                "carry",
                "quick_read_contract",
                "open_first",
            ],
            "paper_execution_contract_checked": True,
            "paper_execution_contract_aligned": True,
            "contract_health_operating_contract_aligned": True,
            "contract_health_paper_execution_contract_aligned": True,
            "contract_health_contracts_are_well_partitioned": True,
        },
    )
    _write_json(
        analysis_dir / "btc_1d_research_stack_operating_brief_latest.json",
        {
            "quick_read_order_version": "research_stack_v2",
            "quick_read_order": [
                "quick_read",
                "stack_roles",
                "stack",
                "near_miss_priority",
                "operating_read",
            ],
        },
    )

    report = build_report(analysis_dir=analysis_dir)

    assert report["regression_lock_test"] == "tests/unit/test_btc_1d_operating_cli_help_contract.py"
    assert report["contract_summary"]["operating_brief_version"] == "operating_v3"
    assert report["contract_summary"]["operating_index_version"] == "operating_v3"
    assert report["contract_summary"]["research_stack_version"] == "research_stack_v2"
    assert report["contract_summary"]["operating_contract_aligned"] is True
    assert report["contract_summary"]["paper_execution_contract_aligned"] is True
    assert report["contract_summary"]["contract_health_aligned"] is True
    assert report["contract_summary"]["research_contract_distinct"] is True
    assert report["contract_summary"]["shared_standard_check_order"] == [
        "practical",
        "research",
        "contract",
        "brief",
    ]
    assert report["contract_verdict"]["contracts_are_well_partitioned"] is True


def test_build_report_fails_when_paper_execution_contract_self_check_drifts(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir / "btc_1d_operating_brief_latest.json",
        {
            "quick_read_order_version": "operating_v3",
            "standard_check_order": ["practical", "research", "contract", "brief"],
            "quick_read_order": ["practical_status", "combined_health", "quick_read_contract", "open_first"],
            "paper_execution_contract_checked": False,
            "paper_execution_contract_aligned": True,
            "contract_health_operating_contract_aligned": True,
            "contract_health_paper_execution_contract_aligned": False,
            "contract_health_contracts_are_well_partitioned": False,
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_index_latest.json",
        {
            "quick_read_order_version": "operating_v3",
            "standard_check_order": ["practical", "research", "contract", "brief"],
            "quick_read_order": ["practical_status", "combined_health", "quick_read_contract", "open_first"],
            "paper_execution_contract_checked": True,
            "paper_execution_contract_aligned": True,
            "contract_health_operating_contract_aligned": True,
            "contract_health_paper_execution_contract_aligned": False,
            "contract_health_contracts_are_well_partitioned": False,
        },
    )
    _write_json(
        analysis_dir / "btc_1d_research_stack_operating_brief_latest.json",
        {
            "quick_read_order_version": "research_stack_v2",
            "quick_read_order": ["quick_read", "stack_roles", "stack", "near_miss_priority", "operating_read"],
        },
    )

    report = build_report(analysis_dir=analysis_dir)

    assert report["contract_summary"]["operating_contract_aligned"] is True
    assert report["contract_summary"]["paper_execution_contract_aligned"] is False
    assert report["contract_summary"]["contract_health_aligned"] is True
    assert report["contract_summary"]["paper_execution_contract_alignment"]["paper_execution_contract_checked"] is False
    assert report["contract_verdict"]["contracts_are_well_partitioned"] is False


def test_build_report_fails_when_contract_health_mirror_drifts(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    _write_json(
        analysis_dir / "btc_1d_operating_brief_latest.json",
        {
            "quick_read_order_version": "operating_v3",
            "standard_check_order": ["practical", "research", "contract", "brief"],
            "quick_read_order": ["practical_status", "combined_health", "quick_read_contract", "open_first"],
            "paper_execution_contract_checked": True,
            "paper_execution_contract_aligned": True,
            "contract_health_operating_contract_aligned": True,
            "contract_health_paper_execution_contract_aligned": False,
            "contract_health_contracts_are_well_partitioned": True,
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_index_latest.json",
        {
            "quick_read_order_version": "operating_v3",
            "standard_check_order": ["practical", "research", "contract", "brief"],
            "quick_read_order": ["practical_status", "combined_health", "quick_read_contract", "open_first"],
            "paper_execution_contract_checked": True,
            "paper_execution_contract_aligned": True,
            "contract_health_operating_contract_aligned": True,
            "contract_health_paper_execution_contract_aligned": True,
            "contract_health_contracts_are_well_partitioned": True,
        },
    )
    _write_json(
        analysis_dir / "btc_1d_research_stack_operating_brief_latest.json",
        {
            "quick_read_order_version": "research_stack_v2",
            "quick_read_order": ["quick_read", "stack_roles", "stack", "near_miss_priority", "operating_read"],
        },
    )

    report = build_report(analysis_dir=analysis_dir)

    assert report["contract_summary"]["operating_contract_aligned"] is True
    assert report["contract_summary"]["paper_execution_contract_aligned"] is True
    assert report["contract_summary"]["contract_health_alignment"]["contract_health_paper_execution_contract_aligned"] is False
    assert report["contract_summary"]["contract_health_aligned"] is False
    assert report["contract_verdict"]["contracts_are_well_partitioned"] is True


def test_render_markdown_contains_contract_sections() -> None:
    rendered = _render_markdown(
        {
            "regression_lock_test": "tests/unit/test_btc_1d_operating_cli_help_contract.py",
            "contracts": [
                {
                    "label": "operating_brief",
                    "path": "analysis_results\\btc_1d_operating_brief_latest.json",
                    "quick_read_order_version": "operating_v3",
                    "standard_check_order": ["practical", "research", "contract", "brief"],
                    "quick_read_order": ["practical_status", "combined_health"],
                },
                {
                    "label": "operating_index",
                    "path": "analysis_results\\btc_1d_operating_index_latest.json",
                    "quick_read_order_version": "operating_v3",
                    "standard_check_order": ["practical", "research", "contract", "brief"],
                    "quick_read_order": ["practical_status", "combined_health"],
                },
                {
                    "label": "research_stack_operating_brief",
                    "path": "analysis_results\\btc_1d_research_stack_operating_brief_latest.json",
                    "quick_read_order_version": "research_stack_v2",
                    "standard_check_order": [],
                    "quick_read_order": ["quick_read", "stack_roles"],
                },
            ],
            "contract_summary": {
                "operating_brief_version": "operating_v3",
                "operating_index_version": "operating_v3",
                "research_stack_version": "research_stack_v2",
                "operating_contract_aligned": True,
                "paper_execution_contract_aligned": True,
                "contract_health_aligned": True,
                "paper_execution_contract_alignment": {
                    "paper_execution_contract_checked": True,
                },
                "contract_health_read": {
                    "operating_brief": {
                        "contract_health_operating_contract_aligned": True,
                        "contract_health_paper_execution_contract_aligned": True,
                        "contract_health_contracts_are_well_partitioned": True,
                    },
                    "operating_index": {
                        "contract_health_operating_contract_aligned": True,
                        "contract_health_paper_execution_contract_aligned": True,
                        "contract_health_contracts_are_well_partitioned": True,
                    },
                },
                "research_contract_distinct": True,
                "shared_standard_check_order": ["practical", "research", "contract", "brief"],
            },
            "contract_verdict": {
                "contracts_are_well_partitioned": True,
                "reason": "Contracts are partitioned as expected.",
            },
        }
    )

    assert "# BTC 1d Quick Read Contract Screen" in rendered
    assert "Operating brief version: `operating_v3`" in rendered
    assert "Research stack version: `research_stack_v2`" in rendered
    assert "Paper execution contract aligned: `True`" in rendered
    assert "Contract health aligned: `True`" in rendered
    assert "Shared standard check order: `['practical', 'research', 'contract', 'brief']`" in rendered
    assert "Regression lock: `tests/unit/test_btc_1d_operating_cli_help_contract.py`" in rendered
    assert "## operating_brief" in rendered
    assert "standard check order: `['practical', 'research', 'contract', 'brief']`" in rendered
    assert "contract health: `{'contract_health_operating_contract_aligned': True, 'contract_health_paper_execution_contract_aligned': True, 'contract_health_contracts_are_well_partitioned': True}`" in rendered
    assert "## research_stack_operating_brief" in rendered


def test_write_latest_aliases_creates_fixed_name_copies(tmp_path: Path) -> None:
    json_path = tmp_path / "btc_1d_quick_read_contract_screen_20260416T000000Z.json"
    md_path = tmp_path / "btc_1d_quick_read_contract_screen_20260416T000000Z.md"
    json_path.write_text('{"ok": true}', encoding="utf-8")
    md_path.write_text("# ok", encoding="utf-8")

    aliases = _write_latest_aliases(json_path, md_path)

    latest_json = Path(aliases["btc_1d_quick_read_contract_screen"])
    latest_md = Path(aliases["btc_1d_quick_read_contract_screen_md"])
    assert latest_json.name == "btc_1d_quick_read_contract_screen_latest.json"
    assert latest_json.read_text(encoding="utf-8") == '{"ok": true}'
    assert latest_md.name == "btc_1d_quick_read_contract_screen_md_latest.md"
    assert latest_md.read_text(encoding="utf-8") == "# ok"
