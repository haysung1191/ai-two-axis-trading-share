from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_dead_family_ledger"

SUMMARY = {
    "as_of_date": "2026-04-17",
    "repo": "momentum",
    "asset_class": "stocks_etfs",
    "strongest": "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on",
    "ledgers": [
        {
            "family": "quality-headline hybrid",
            "status": "dead",
            "best_tested_point": "hybrid_quality85_skipentry_top25_mid75",
            "headline_signal": "+1.56%p CAGR, +0.25%p MDD, walk-forward 4 positive / 0 negative",
            "kill_reason": "Sharpe delta -0.0394 and both walk-forward/cost Sharpe stayed clearly negative",
            "retry_rule": "do not retry unless the hybrid changes a different robustness axis than recipient plus skip-entry mixing",
        },
        {
            "family": "risk-on exposure",
            "status": "dead",
            "best_tested_point": "risk_on_exposure_106",
            "headline_signal": "none; scanned points stayed weaker than strongest",
            "kill_reason": "CAGR, walk-forward, and cost all weakened together",
            "retry_rule": "do not retry simple exposure bumps around 1.02-1.06",
        },
        {
            "family": "risk-off tightening",
            "status": "dead",
            "best_tested_point": "risk_off_tighten_sector075",
            "headline_signal": "+0.0150 Sharpe",
            "kill_reason": "headline strength collapsed; CAGR delta -1.53%p with 1 positive / 3 negative walk-forward windows",
            "retry_rule": "do not retry tighter sector risk-off without a separate offsetting alpha source",
        },
        {
            "family": "entry filter",
            "status": "dead",
            "best_tested_point": "entry_filter_soft_r1m20_pen50",
            "headline_signal": "+0.50%p MDD improvement",
            "kill_reason": "CAGR and Sharpe both weakened and walk-forward stayed 2 positive / 2 negative",
            "retry_rule": "do not retry simple entrant overheat penalties around soft r1m 0.20",
        },
        {
            "family": "hold buffer",
            "status": "no-op",
            "best_tested_point": "hold_buffer1 / hold_buffer2",
            "headline_signal": "identical to strongest",
            "kill_reason": "selection did not change at all",
            "retry_rule": "do not retry hold-buffer variants unless the base selection logic itself changes",
        },
        {
            "family": "position cap",
            "status": "dead",
            "best_tested_point": "position_cap_us4",
            "headline_signal": "+2.40%p MDD improvement and lower turnover",
            "kill_reason": "CAGR delta -22.78%p and walk-forward 0 positive / 4 negative",
            "retry_rule": "do not retry harder US cap reductions around 5 -> 4",
        },
        {
            "family": "sector cap relaxation",
            "status": "dead",
            "best_tested_point": "sector_cap3",
            "headline_signal": "+2.18%p MDD improvement and lower turnover",
            "kill_reason": "CAGR delta -6.07%p and walk-forward 0 positive / 4 negative",
            "retry_rule": "do not retry looser sector cap around 2 -> 3",
        },
        {
            "family": "flow filter",
            "status": "dead",
            "best_tested_point": "flow_filter_uscap035",
            "headline_signal": "none",
            "kill_reason": "CAGR delta -33.00%p, Sharpe delta -0.3538, cost and residual both collapsed",
            "retry_rule": "do not retry simple US flow caps near 0.35",
        },
        {
            "family": "soft blacklist",
            "status": "dead",
            "best_tested_point": "soft_blacklist_top3_pen85",
            "headline_signal": "+0.20%p MDD improvement and lower winner dependence",
            "kill_reason": "CAGR delta -2.05%p and Sharpe delta -0.0824",
            "retry_rule": "do not retry direct soft penalties on PLTR/NVDA/MU without a compensating new alpha source",
        },
        {
            "family": "dynamic bonus sizing",
            "status": "dead",
            "best_tested_point": "dynamic_bonus_tight14_if_top42",
            "headline_signal": "slightly lower turnover",
            "kill_reason": "CAGR delta -1.51%p and fragility actually worsened",
            "retry_rule": "do not retry simple bonus-tightening rules based only on top2 concentration",
        },
        {
            "family": "KR unknown exclusion",
            "status": "no-op",
            "best_tested_point": "exclude_kr_unknown_strongest",
            "headline_signal": "identical to strongest",
            "kill_reason": "selection did not change at all",
            "retry_rule": "do not retry this family unless KR unknown names start entering the strongest book",
        },
        {
            "family": "liquidity gate",
            "status": "dead",
            "best_tested_point": "liquidity_gate_relvol105",
            "headline_signal": "none",
            "kill_reason": "CAGR delta -42.03%p, MDD got worse, Sharpe collapsed, turnover rose",
            "retry_rule": "do not retry min_rel_volume around 1.05 or higher as a mainline branch search axis",
        },
        {
            "family": "book size",
            "status": "no-op",
            "best_tested_point": "book_size10_strongest / book_size8_strongest",
            "headline_signal": "identical to strongest",
            "kill_reason": "selection and outcome did not change at all",
            "retry_rule": "do not retry book-size toggles unless the base selection cardinality logic changes",
        },
        {
            "family": "winner cap",
            "status": "dead",
            "best_tested_point": "top1_weight_cap18",
            "headline_signal": "+0.335%p residual ex PLTR/NVDA/MU",
            "kill_reason": "CAGR delta -7.23%p, MDD worsened, Sharpe delta -0.0877, turnover rose",
            "retry_rule": "do not retry simple post-weight top1 caps around 18% as a mainline branch search axis",
        },
        {
            "family": "mid-book recipient",
            "status": "dead",
            "best_tested_point": "bonus_recipient_top1_fourth_85_15",
            "headline_signal": "+2.40%p CAGR and +1.82%p cost CAGR",
            "kill_reason": "MDD worsened, walk-forward stayed 2 positive / 2 negative, and cost Sharpe stayed negative",
            "retry_rule": "do not retry simple top1 plus fourth recipient variants without a new robustness offset",
        },
        {
            "family": "tail penalty shape",
            "status": "dead",
            "best_tested_point": "tail_penalty_shape_pow075",
            "headline_signal": "+7.66%p CAGR and +6.87%p cost CAGR",
            "kill_reason": "MDD worsened by -8.39%p and Sharpe delta fell to -0.1799",
            "retry_rule": "do not retry stronger tail-penalty curves that only push the branch into redistribution-like behavior",
        },
        {
            "family": "book ordering",
            "status": "dead",
            "best_tested_point": "book_order_flow_first_weight_map",
            "headline_signal": "lower concentration",
            "kill_reason": "CAGR slipped, MDD worsened, Sharpe delta -0.0850, and cost weakened clearly",
            "retry_rule": "do not retry FlowScore-first weight remapping inside the selected book",
        },
        {
            "family": "rebalance timing",
            "status": "dead",
            "best_tested_point": "rebalance_every_2m",
            "headline_signal": "+9.04%p MDD improvement and +0.3821 Sharpe",
            "kill_reason": "CAGR delta -25.13%p and cost CAGR delta -18.45%p",
            "retry_rule": "do not retry slower rebalance cadence as a mainline strongest search axis",
        },
        {
            "family": "risk budget",
            "status": "dead",
            "best_tested_point": "risk_budget_toptrim10_to_tail",
            "headline_signal": "+0.049%p residual ex PLTR/NVDA/MU",
            "kill_reason": "CAGR delta -4.09%p, MDD worsened, Sharpe delta -0.0835, and walk-forward fell to 1 positive / 3 negative",
            "retry_rule": "do not retry simple top-trim to tail risk-budget transfers",
        },
        {
            "family": "signal smoothing",
            "status": "dead",
            "best_tested_point": "signal_smoothing_sqrt_weights",
            "headline_signal": "lower concentration",
            "kill_reason": "CAGR delta -10.38%p, MDD worsened, Sharpe delta -0.1186, and cost weakened materially",
            "retry_rule": "do not retry generic sqrt-style smoothing of the strongest weight map",
        },
        {
            "family": "cost-aware incumbency",
            "status": "no-op",
            "best_tested_point": "cost_aware_incumbent_bonus05",
            "headline_signal": "identical to strongest",
            "kill_reason": "incumbent bonus did not alter the realized book or outcome",
            "retry_rule": "do not retry simple incumbent bonus overlays unless the rebalance admission logic changes",
        },
        {
            "family": "sector rotation trigger",
            "status": "dead",
            "best_tested_point": "sector_rotation_trigger_alt_sector03",
            "headline_signal": "sector concentration eased slightly",
            "kill_reason": "CAGR delta -0.24%p, MDD worsened, Sharpe delta -0.0425, and cost weakened",
            "retry_rule": "do not retry same-sector handoff triggers near 0.03",
        },
        {
            "family": "cross-market handoff",
            "status": "dead",
            "best_tested_point": "cross_market_handoff_alt_market03",
            "headline_signal": "+0.046%p residual ex PLTR/NVDA/MU",
            "kill_reason": "CAGR delta -0.85%p, MDD worsened, Sharpe delta -0.0402, and walk-forward fell to 1 positive / 3 negative",
            "retry_rule": "do not retry same-market handoff triggers near 0.03",
        },
        {
            "family": "symbol memory",
            "status": "no-op",
            "best_tested_point": "symbol_memory_top1_bonus03",
            "headline_signal": "identical to strongest",
            "kill_reason": "memory bonus did not alter the realized book or outcome",
            "retry_rule": "do not retry simple top1 memory bonuses unless the rank transition logic changes",
        },
        {
            "family": "dual-score gating",
            "status": "dead",
            "best_tested_point": "dual_score_gate_top2_flowtop3",
            "headline_signal": "slightly positive walk-forward CAGR",
            "kill_reason": "CAGR delta -1.27%p, Sharpe delta -0.0320, cost weakened, and residual turned negative",
            "retry_rule": "do not retry momentum-plus-flow admission gates without a truly different payout rule",
        },
        {
            "family": "state-mixed ranking",
            "status": "dead",
            "best_tested_point": "state_mixed_rank_flow30_if_top242",
            "headline_signal": "+0.0008 walk-forward Sharpe delta",
            "kill_reason": "CAGR delta -1.50%p, Sharpe delta -0.0348, cost weakened, and fragility got worse",
            "retry_rule": "do not retry top2-concentration-triggered mixed ranking overlays",
        },
        {
            "family": "two-stage weight map",
            "status": "dead",
            "best_tested_point": "two_stage_weight_map_top58_rest42",
            "headline_signal": "+0.185%p residual ex PLTR/NVDA/MU",
            "kill_reason": "CAGR delta -7.80%p, MDD worsened, Sharpe delta -0.1292, and walk-forward fell to 1 positive / 3 negative",
            "retry_rule": "do not retry bucketized top-versus-rest weight maps around 58/42",
        },
        {
            "family": "conditional tail count",
            "status": "dead",
            "best_tested_point": "conditional_tail_count4_if_top242",
            "headline_signal": "+6.53%p CAGR and +5.85%p cost CAGR",
            "kill_reason": "MDD worsened by -8.46%p and Sharpe delta fell to -0.1827",
            "retry_rule": "do not retry top2-concentration-triggered tail-count compression without a separate drawdown control",
        },
        {
            "family": "conditional bonus size",
            "status": "dead",
            "best_tested_point": "conditional_bonus14_if_top242",
            "headline_signal": "slightly lower turnover",
            "kill_reason": "CAGR delta -2.81%p, Sharpe delta -0.0387, and walk-forward stayed 0 positive / 3 negative",
            "retry_rule": "do not retry conditional bonus tightening around 0.14 if based only on top2 concentration",
        },
        {
            "family": "exposure ladder",
            "status": "dead",
            "best_tested_point": "exposure_ladder_top26_top18",
            "headline_signal": "lower concentration",
            "kill_reason": "CAGR delta -16.16%p, MDD worsened, Sharpe delta -0.1815, and cost weakened materially",
            "retry_rule": "do not retry explicit top1/top2 cap ladders as a strongest replacement axis",
        },
        {
            "family": "candidate admission",
            "status": "dead",
            "best_tested_point": "candidate_admission_flow_floor0",
            "headline_signal": "none",
            "kill_reason": "CAGR delta -5.01%p, MDD worsened, Sharpe delta -0.1132, and walk-forward fell to 0 positive / 4 negative",
            "retry_rule": "do not retry simple negative-flow admission bans inside the realized book",
        },
        {
            "family": "cash sleeve",
            "status": "dead",
            "best_tested_point": "cash_sleeve_toptrim05 / state_cash_top2conc42_trim05",
            "headline_signal": "slightly higher Sharpe and lower turnover",
            "kill_reason": "both static and state-dependent cash trims weakened CAGR and failed walk-forward robustness",
            "retry_rule": "do not retry cash sleeve overlays unless the cash decision is paired with a new alpha source",
        },
        {
            "family": "rank stability",
            "status": "dead",
            "best_tested_point": "rank_stability_bonus_third_if_gap015",
            "headline_signal": "+0.042%p residual ex PLTR/NVDA/MU",
            "kill_reason": "CAGR slipped, MDD worsened, Sharpe delta -0.0425, and cost weakened",
            "retry_rule": "do not retry gap-based rank-sharing between first and third names around 0.15 / 0.03",
        },
    ],
    "ledger_verdict": "recent search has enough evidence to stop repeating these dead or no-op families under the current strongest",
}


def _build_markdown(summary: dict) -> str:
    lines = [
        "# Split Models Dead Family Ledger",
        "",
        "## Purpose",
        "",
        "- record which family axes are dead or no-op under the current strongest",
        "- reduce repeated overnight search on already disproven branches",
        "",
        "## Current strongest",
        "",
        f"- `{summary['strongest']}`",
        "",
        "## Ledger",
        "",
    ]

    for row in summary["ledgers"]:
        lines.extend(
            [
                f"- {row['family']}: `{row['status']}`",
                f"  - best tested point: `{row['best_tested_point']}`",
                f"  - strongest signal: `{row['headline_signal']}`",
                f"  - kill reason: `{row['kill_reason']}`",
                f"  - retry rule: `{row['retry_rule']}`",
            ]
        )

    lines.extend(
        [
            "",
            "## Verdict",
            "",
            f"- {summary['ledger_verdict']}",
            "- future search should favor genuinely different families instead of recycling these axes",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "dead_family_ledger_summary.json").write_text(
        json.dumps(SUMMARY, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "dead_family_ledger.md").write_text(
        _build_markdown(SUMMARY), encoding="utf-8"
    )
    print(json.dumps(SUMMARY, indent=2))


if __name__ == "__main__":
    main()
