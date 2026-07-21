from __future__ import annotations

import json
from pathlib import Path

from scripts.publish_btc_1d_operator_dashboard_site import publish_dashboard_site


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_publish_dashboard_site_writes_docs_snapshot(tmp_path: Path) -> None:
    analysis_dir = tmp_path / "analysis_results"
    docs_dir = tmp_path / "docs"

    _write_json(
        analysis_dir / "btc_1d_latest_summary_latest.json",
        {
            "candidate": "btc_1d_prod_candidate",
            "shadow_decision": "ready",
            "carry": {"decision": "pass", "sharpe": 1.1, "cagr": 0.2, "max_drawdown": 0.1},
            "survivability": {"decision": "pass", "sharpe": 1.0, "cagr": 0.18, "max_drawdown": 0.12},
            "walk_forward": {"passed": True, "oos_sharpe": 0.8, "oos_cagr": 0.1, "oos_max_drawdown": 0.13},
            "friction": {"decision": "pass", "heaviest_level_bps": 20, "heaviest_level_sharpe": 0.75},
            "eth_cross_check": {"symbol": "ETHUSDT", "pass_rate": 0.5},
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_index_latest.json",
        {
            "practical_status_label": "carryable_candidate",
            "combined_health_line": "combined health",
            "research_stack_status": "research healthy",
            "execution_contract_health_line": "execution contract health",
            "execution_contract_read": "execution contract read",
            "paper_execution_read": "paper execution read",
            "paper_execution_contract_aligned": True,
            "paper_exit_duplicate_run": False,
            "paper_ledger_consistent": True,
            "paper_ledger_snapshot_read": "paper ledger",
            "contract_health_aligned": True,
        },
    )
    _write_json(
        analysis_dir / "btc_1d_operating_brief_latest.json",
        {"contract_health_line": "contract health line"},
    )
    _write_json(
        analysis_dir / "btc_1d_quick_read_contract_screen_latest.json",
        {
            "contract_summary": {
                "operating_contract_aligned": True,
                "paper_execution_contract_aligned": True,
                "contract_health_aligned": True,
            },
            "contract_verdict": {"contracts_are_well_partitioned": True},
        },
    )
    _write_json(
        analysis_dir / "btc_1d_execution_contract_screen_latest.json",
        {
            "execution_contract_summary": {
                "paper_ledger_snapshot_summary_aligned": True,
                "paper_execution_contract_aligned_summary_aligned": True,
            },
            "execution_contract_verdict": {"execution_contract_aligned": True},
        },
    )
    _write_json(
        analysis_dir / "btc_1d_paper_nightly_summary_latest.json",
        {
            "intent_count": 1,
            "signed_request_count": 1,
            "paper_applied_count": 1,
            "paper_duplicate_count": 0,
            "paper_closed_count": 1,
            "paper_open_count": 0,
            "paper_ledger_snapshot_read": "paper ledger",
        },
    )

    paths = publish_dashboard_site(analysis_dir=analysis_dir, docs_dir=docs_dir)

    dashboard_index = Path(paths["dashboard_index_html"])
    dashboard_json = Path(paths["dashboard_json"])
    dashboard_md = Path(paths["dashboard_md"])
    docs_index = Path(paths["docs_index_html"])

    assert dashboard_index.exists()
    assert dashboard_json.exists()
    assert dashboard_md.exists()
    assert docs_index.exists()
    assert "BTC 1d Operator Dashboard" in dashboard_index.read_text(encoding="utf-8")
    assert "dashboard_ready" in dashboard_json.read_text(encoding="utf-8")
    assert "# BTC 1d Operator Dashboard" in dashboard_md.read_text(encoding="utf-8")
    assert 'url=./dashboard/' in docs_index.read_text(encoding="utf-8")
