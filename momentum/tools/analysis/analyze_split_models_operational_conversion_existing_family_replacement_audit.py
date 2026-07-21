from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
OUTPUT_ROOT = ROOT / "output"
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_existing_family_replacement_audit"
OPERATING_BASELINE_MDD = -0.25241596238415986


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _candidate_rows(data: dict) -> list[dict]:
    rows: list[dict] = []
    for key in ("ranked_rows", "rows"):
        value = data.get(key)
        if isinstance(value, list):
            rows.extend(row for row in value if isinstance(row, dict))
    if data.get("best_variant"):
        rows.append(
            {
                "variant": data.get("best_variant"),
                "cagr": data.get("best_cagr"),
                "mdd": data.get("best_mdd"),
                "sharpe": data.get("best_sharpe"),
                "negative_cagr_windows": data.get("best_negative_cagr_windows"),
            }
        )
    return rows


def _norm_row(row: dict, source: Path) -> dict | None:
    variant = row.get("Variant") or row.get("variant")
    cagr = row.get("CAGR", row.get("cagr"))
    mdd = row.get("MDD", row.get("mdd"))
    sharpe = row.get("Sharpe", row.get("sharpe"))
    neg_wf = row.get("NegativeCAGRWindows", row.get("negative_cagr_windows"))
    try:
        cagr_f = float(cagr)
        mdd_f = float(mdd)
    except Exception:
        return None
    return {
        "variant": str(variant),
        "cagr": cagr_f,
        "mdd": mdd_f,
        "sharpe": None if sharpe is None else float(sharpe),
        "negative_cagr_windows": neg_wf,
        "source": str(source),
    }


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion Existing Family Replacement Audit",
        "",
        f"Generated: `{summary['generated_at']}`",
        "",
        "## Status",
        "",
        f"- Decision: `{summary['audit_decision']}`",
        f"- Eligible candidate count: `{summary['eligible_candidate_count']}`",
        "",
        "## Eligible Candidates",
        "",
        "| Variant | CAGR | MDD | Neg WF | Source |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for row in summary["eligible_candidates"]:
        neg = "n/a" if row["negative_cagr_windows"] is None else str(row["negative_cagr_windows"])
        lines.append(
            f"| `{row['variant']}` | {row['cagr']:.2%} | {row['mdd']:.2%} | {neg} | `{row['source']}` |"
        )
    lines.extend(["", "## Next Action", "", f"- {summary['next_action']}", ""])
    return "\n".join(lines)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    eligible: list[dict] = []
    for path in OUTPUT_ROOT.rglob("*summary.json"):
        if "operational_conversion" not in str(path):
            continue
        try:
            data = _load_json(path)
        except Exception:
            continue
        for row in _candidate_rows(data):
            norm = _norm_row(row, path)
            if norm and norm["mdd"] > OPERATING_BASELINE_MDD:
                eligible.append(norm)
    eligible = sorted(
        eligible,
        key=lambda row: (
            row["negative_cagr_windows"] if row["negative_cagr_windows"] is not None else 999,
            -row["mdd"],
            -row["cagr"],
        ),
    )
    unique: list[dict] = []
    seen: set[str] = set()
    for row in eligible:
        key = row["variant"]
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    replacement_candidates = [
        row
        for row in unique
        if row["variant"] not in {
            "tail_release_top25_mid75_pen35_floor25_trim22_window_extsymbol_trim100",
            "tail_release_top25_mid75_pen35_floor25_trim22_state_extsymbol_sym09_sector28_trim100_max08",
        }
        and row["negative_cagr_windows"] in {0, None}
    ]
    summary = {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "audit_decision": "NO_EXISTING_FAMILY_REPLACEMENT_READY"
        if not replacement_candidates
        else "EXISTING_FAMILY_REPLACEMENT_CANDIDATES_FOUND",
        "operating_baseline_mdd": OPERATING_BASELINE_MDD,
        "eligible_candidate_count": len(unique),
        "eligible_candidates": unique,
        "replacement_candidates": replacement_candidates,
        "next_action": (
            "Create a new rolling-risk or candidate-family replacement experiment; existing eligible outputs only contain the fixed-window defense and the state-condition defense that still fails start-shift."
            if not replacement_candidates
            else "Register the strongest replacement candidate for OOS validation."
        ),
        "safety": {
            "paper_enabled": False,
            "live_enabled": False,
            "broker_submit_allowed": False,
            "order_intent_created": False,
        },
    }
    (OUTPUT_DIR / "existing_family_replacement_audit_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "existing_family_replacement_audit.md").write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
