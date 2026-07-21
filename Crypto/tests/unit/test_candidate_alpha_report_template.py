from __future__ import annotations

import json
from pathlib import Path

from scripts.candidate_alpha_report_template import build_contract_status, build_report_template


def test_report_template_includes_contract_status_and_disclosures(tmp_path: Path) -> None:
    artifact_dir = tmp_path / 'artifact'
    artifact_dir.mkdir()
    backtest_report = {
        'strategy_name': 'krw_btc_swing_trend',
        'trades': 10,
        'sharpe': 0.1,
        'max_drawdown': 0.2,
        'win_rate': 0.5,
        'cagr': 0.01,
        'equity_curve': [1.0, 1.1],
        'equity_timestamps': ['2026-01-01T00:00:00+00:00', '2026-01-01T04:00:00+00:00'],
        'trade_ledger': [],
        'symbols': ['KRW-BTC'],
    }
    contract = build_contract_status(backtest_report)
    post = {
        'artifact': {'artifact_dir': str(artifact_dir)},
        'join_coverage': {
            'matched_label_count': 10,
            'artifact_observation_count': 10,
            'matched_label_ratio': 1.0,
            'matched_trade_label_count': 0,
            'trade_observation_count': 0,
            'matched_trade_label_ratio': 0.0,
            'used_direct_timestamps': True,
            'timestamp_start': '2026-01-01T00:00:00+00:00',
            'timestamp_end': '2026-01-02T00:00:00+00:00',
        },
        'bucket_summary': {
            'avoidance_regime': {'observation_count': 1, 'mean_return': 0.0, 'worst_drawdown': 0.0, 'trade_count': None, 'win_rate': None},
            'non_avoidance_regime': {'observation_count': 2, 'mean_return': 0.1, 'worst_drawdown': -0.1, 'trade_count': None, 'win_rate': None},
        },
        'boundary': {
            'what_it_does': 'Attaches Candidate Alpha descriptive labels to an existing backtest result by timestamp join only.',
            'what_it_does_not_do': 'Does not alter strategy signals, execution, or runtime behavior.',
        },
    }

    report = build_report_template(post, contract)

    assert report['artifact_quality']['artifact_type'] == 'enriched-standard'
    assert 'Candidate Alpha is used here as a descriptive regime label only.' in report['confidence_warning']['required_disclosures']
    assert 'execution gating justification' in report['regime_analysis']['forbidden_conclusions']
