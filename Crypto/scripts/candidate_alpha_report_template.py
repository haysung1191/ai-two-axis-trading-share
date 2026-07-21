from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REQUIRED_BACKTEST_FIELDS = [
    'strategy_name',
    'trades',
    'sharpe',
    'max_drawdown',
    'win_rate',
    'cagr',
    'equity_curve',
    'equity_timestamps',
    'trade_ledger',
    'symbols',
]
OPTIONAL_BACKTEST_FIELDS = [
    'equity_curve_summary',
    'sharpe_mean',
    'sharpe_std',
    'drawdown_mean',
    'drawdown_worst',
    'regime_metrics',
    'failed_thresholds',
]


def _latest_post_analysis(analysis_dir: Path) -> Path:
    candidates = sorted(
        analysis_dir.glob('candidate_alpha_post_analysis_*.json'),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError('No Candidate Alpha post-analysis artifact found')
    return candidates[0]


def load_post_analysis(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8'))


def load_backtest_report(artifact_dir: Path) -> dict[str, Any]:
    path = artifact_dir / 'backtest_report.json'
    if not path.exists():
        raise FileNotFoundError(f'Missing backtest_report.json in {artifact_dir}')
    return json.loads(path.read_text(encoding='utf-8'))


def build_contract_status(backtest_report: dict[str, Any]) -> dict[str, Any]:
    required_present = [field for field in REQUIRED_BACKTEST_FIELDS if field in backtest_report]
    required_missing = [field for field in REQUIRED_BACKTEST_FIELDS if field not in backtest_report]
    optional_present = [field for field in OPTIONAL_BACKTEST_FIELDS if field in backtest_report]
    status = 'enriched-standard' if not required_missing else 'legacy-fallback'
    return {
        'artifact_contract_status': status,
        'required_fields_present': required_present,
        'required_fields_missing': required_missing,
        'optional_fields_present': optional_present,
    }


def build_required_disclosures(post: dict[str, Any], contract: dict[str, Any]) -> list[str]:
    coverage = post['join_coverage']
    disclosures = [
        'Candidate Alpha is used here as a descriptive regime label only.',
        'This report attaches labels by timestamp join after the backtest; it does not alter signal generation or execution.',
        f"Artifact contract status: {contract['artifact_contract_status']}.",
        f"Per-bar join coverage: {coverage['matched_label_count']} / {coverage['artifact_observation_count']} (ratio {coverage['matched_label_ratio']}).",
        (
            f"Trade-label coverage: {coverage['matched_trade_label_count']} / {coverage['trade_observation_count']} "
            f"(ratio {coverage['matched_trade_label_ratio']})."
            if coverage['trade_observation_count'] is not None
            else 'Trade-label coverage: unavailable.'
        ),
        f"Direct artifact timestamps used: {coverage['used_direct_timestamps']}.",
        (
            f"Missing required fields: {', '.join(contract['required_fields_missing'])}."
            if contract['required_fields_missing']
            else 'Missing required fields: none.'
        ),
        'Any regime comparison in this report is descriptive and not a deployability claim.',
    ]
    return disclosures


def build_report_template(post: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    disclosures = build_required_disclosures(post, contract)
    return {
        'generated_at': datetime.now(tz=UTC).isoformat(),
        'artifact_quality': {
            'artifact_type': contract['artifact_contract_status'],
            'artifact_dir': post['artifact']['artifact_dir'],
            'required_fields_present': contract['required_fields_present'],
            'required_fields_missing': contract['required_fields_missing'],
            'optional_fields_present': contract['optional_fields_present'],
        },
        'timestamp_join_quality': post['join_coverage'],
        'regime_analysis': {
            'candidate_alpha_role': 'descriptive regime label only',
            'regime_buckets': ['avoidance_regime', 'non_avoidance_regime'],
            'allowed_conclusions': [
                'descriptive regime differences in returns, drawdowns, and trade quality',
                'regime informativeness as a research segmentation tool',
            ],
            'forbidden_conclusions': [
                'execution gating justification',
                'tradable-edge claim',
                'live or simulated entry/exit control',
            ],
            'boundary': post['boundary'],
        },
        'minimum_metrics': post['bucket_summary'],
        'confidence_warning': {
            'artifact_confidence': 'high' if contract['artifact_contract_status'] == 'enriched-standard' and post['join_coverage']['used_direct_timestamps'] else 'lower',
            'trade_level_confidence': 'available' if post['join_coverage']['matched_trade_label_ratio'] > 0 else 'unavailable',
            'required_disclosures': disclosures,
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    aq = report['artifact_quality']
    jq = report['timestamp_join_quality']
    ra = report['regime_analysis']
    mm = report['minimum_metrics']
    cw = report['confidence_warning']
    a = mm['avoidance_regime']
    n = mm['non_avoidance_regime']
    lines = [
        '# Candidate Alpha Research Report Template',
        '',
        '## 1. Artifact Quality',
        f"- artifact_type: {aq['artifact_type']}",
        f"- artifact_dir: {aq['artifact_dir']}",
        f"- required_fields_present: {aq['required_fields_present']}",
        f"- required_fields_missing: {aq['required_fields_missing']}",
        f"- optional_fields_present: {aq['optional_fields_present']}",
        '',
        '## 2. Timestamp / Join Quality',
        f"- matched_label_ratio: {jq['matched_label_ratio']}",
        f"- matched_trade_label_ratio: {jq['matched_trade_label_ratio']}",
        f"- used_direct_timestamps: {jq['used_direct_timestamps']}",
        f"- timestamp_start: {jq['timestamp_start']}",
        f"- timestamp_end: {jq['timestamp_end']}",
        '',
        '## 3. Regime Analysis',
        f"- candidate_alpha_role: {ra['candidate_alpha_role']}",
        f"- allowed_conclusions: {ra['allowed_conclusions']}",
        f"- forbidden_conclusions: {ra['forbidden_conclusions']}",
        f"- boundary: {ra['boundary']['what_it_does_not_do']}",
        '',
        '## 4. Minimum Metrics',
        '- avoidance_regime:',
        f"  observation_count={a['observation_count']}, mean_return={a['mean_return']}, worst_drawdown={a['worst_drawdown']}, trade_count={a['trade_count']}, win_rate={a['win_rate']}",
        '- non_avoidance_regime:',
        f"  observation_count={n['observation_count']}, mean_return={n['mean_return']}, worst_drawdown={n['worst_drawdown']}, trade_count={n['trade_count']}, win_rate={n['win_rate']}",
        '',
        '## 5. Confidence Warning',
        f"- artifact_confidence: {cw['artifact_confidence']}",
        f"- trade_level_confidence: {cw['trade_level_confidence']}",
        '- required_disclosures:',
    ]
    lines.extend([f'  - {item}' for item in cw['required_disclosures']])
    return '\n'.join(lines) + '\n'


def run_candidate_alpha_report_template(analysis_dir: Path, *, post_analysis_path: Path | None = None) -> dict[str, Path | dict[str, Any]]:
    selected = post_analysis_path or _latest_post_analysis(analysis_dir)
    post = load_post_analysis(selected)
    artifact_dir = Path(post['artifact']['artifact_dir'])
    backtest_report = load_backtest_report(artifact_dir)
    contract = build_contract_status(backtest_report)
    report = build_report_template(post, contract)

    stamp = datetime.now(tz=UTC).strftime('%Y%m%dT%H%M%SZ')
    json_path = analysis_dir / f'candidate_alpha_report_template_{stamp}.json'
    md_path = analysis_dir / f'candidate_alpha_report_template_{stamp}.md'
    json_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    md_path.write_text(render_markdown(report), encoding='utf-8')
    return {'report_json_path': json_path, 'report_md_path': md_path, 'report': report}


def main() -> None:
    parser = argparse.ArgumentParser(description='Generate a standardized Candidate Alpha research report skeleton from an existing post-analysis artifact.')
    parser.add_argument('--analysis-dir', default='analysis_results')
    parser.add_argument('--post-analysis-path', default=None)
    args = parser.parse_args()

    artifacts = run_candidate_alpha_report_template(
        Path(args.analysis_dir),
        post_analysis_path=Path(args.post_analysis_path) if args.post_analysis_path else None,
    )
    print(json.dumps({
        'report_json_path': str(artifacts['report_json_path']),
        'report_md_path': str(artifacts['report_md_path']),
        'artifact_quality': artifacts['report']['artifact_quality'],
        'timestamp_join_quality': artifacts['report']['timestamp_join_quality'],
        'confidence_warning': artifacts['report']['confidence_warning'],
    }, indent=2))


if __name__ == '__main__':
    main()
