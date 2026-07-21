from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@dataclass(frozen=True)
class CandidateAlphaSemanticArtifacts:
    memo_json_path: Path
    memo_md_path: Path
    memo: dict[str, Any]


def _latest_analysis_frame(analysis_dir: Path) -> Path:
    candidates = sorted(
        analysis_dir.glob("candidate_alpha_regime_frame_*.csv"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError("No Candidate Alpha frame artifact found")
    return candidates[0]


def load_candidate_alpha_frame(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, parse_dates=["timestamp"]).set_index("timestamp")
    valid = frame.dropna(
        subset=[
            "dislocation_std_72",
            "delta_dislocation_std_72",
            "krw_usdt_abs_return_mean_72",
            "forward_return_1h",
            "forward_return_4h",
            "forward_vol_1h",
            "forward_vol_4h",
        ]
    ).copy()
    valid["tradable_regime"] = valid["tradable_regime"].astype(bool)
    valid["avoidance_regime"] = valid["avoidance_regime"].astype(bool)
    return valid


def _regime_stats(subset: pd.DataFrame, mask: pd.Series) -> dict[str, Any]:
    frame = subset.loc[mask].copy()
    if frame.empty:
        return {
            "count": 0,
            "mean_forward_return_1h": None,
            "mean_forward_return_4h": None,
            "mean_forward_vol_1h": None,
            "mean_forward_vol_4h": None,
        }
    return {
        "count": int(len(frame)),
        "mean_forward_return_1h": float(frame["forward_return_1h"].mean()),
        "mean_forward_return_4h": float(frame["forward_return_4h"].mean()),
        "mean_forward_vol_1h": float(frame["forward_vol_1h"].mean()),
        "mean_forward_vol_4h": float(frame["forward_vol_4h"].mean()),
    }


def _comparison_block(subset: pd.DataFrame) -> dict[str, Any]:
    tradable = _regime_stats(subset, subset["tradable_regime"])
    avoidance = _regime_stats(subset, subset["avoidance_regime"])
    return {
        "tradable": tradable,
        "avoidance": avoidance,
        "diff_avoidance_minus_tradable": {
            "forward_return_1h": None
            if tradable["mean_forward_return_1h"] is None or avoidance["mean_forward_return_1h"] is None
            else float(avoidance["mean_forward_return_1h"] - tradable["mean_forward_return_1h"]),
            "forward_return_4h": None
            if tradable["mean_forward_return_4h"] is None or avoidance["mean_forward_return_4h"] is None
            else float(avoidance["mean_forward_return_4h"] - tradable["mean_forward_return_4h"]),
            "forward_vol_1h": None
            if tradable["mean_forward_vol_1h"] is None or avoidance["mean_forward_vol_1h"] is None
            else float(avoidance["mean_forward_vol_1h"] - tradable["mean_forward_vol_1h"]),
            "forward_vol_4h": None
            if tradable["mean_forward_vol_4h"] is None or avoidance["mean_forward_vol_4h"] is None
            else float(avoidance["mean_forward_vol_4h"] - tradable["mean_forward_vol_4h"]),
        },
    }


def build_candidate_alpha_semantic_memo(frame: pd.DataFrame, *, chunks: int = 3) -> dict[str, Any]:
    full_sample = _comparison_block(frame)

    chunk_labels = pd.qcut(pd.Series(range(len(frame)), index=frame.index), q=chunks, labels=[f"chunk_{i+1}" for i in range(chunks)])
    subperiods: dict[str, Any] = {}
    pos_4h = 0
    pos_1h = 0
    for label in [f"chunk_{i+1}" for i in range(chunks)]:
        comparison = _comparison_block(frame[chunk_labels == label])
        subperiods[label] = comparison
        diff_1h = comparison["diff_avoidance_minus_tradable"]["forward_return_1h"]
        diff_4h = comparison["diff_avoidance_minus_tradable"]["forward_return_4h"]
        if diff_1h is not None and diff_1h > 0:
            pos_1h += 1
        if diff_4h is not None and diff_4h > 0:
            pos_4h += 1

    full_diff_1h = full_sample["diff_avoidance_minus_tradable"]["forward_return_1h"]
    full_diff_4h = full_sample["diff_avoidance_minus_tradable"]["forward_return_4h"]
    full_vol_diff_4h = full_sample["diff_avoidance_minus_tradable"]["forward_vol_4h"]

    likely_real_signal = bool(full_diff_4h is not None and full_diff_4h > 0 and pos_4h >= 2)
    should_invert = bool(likely_real_signal and full_diff_4h > 0 and pos_1h >= 2)

    if likely_real_signal and should_invert:
        final_decision = "continue but redefine as avoidance-regime detection"
    elif likely_real_signal:
        final_decision = "continue"
    else:
        final_decision = "stop"

    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "coverage": {
            "valid_rows": int(len(frame)),
            "start": frame.index.min().isoformat() if not frame.empty else None,
            "end": frame.index.max().isoformat() if not frame.empty else None,
            "chunks": chunks,
        },
        "full_sample": full_sample,
        "subperiods": subperiods,
        "interpretation": {
            "likely_real_signal": likely_real_signal,
            "keep_current_labels": False if should_invert else not likely_real_signal,
            "invert_label_semantics": should_invert,
            "full_sample_avoidance_minus_tradable_1h": full_diff_1h,
            "full_sample_avoidance_minus_tradable_4h": full_diff_4h,
            "full_sample_avoidance_minus_tradable_vol_4h": full_vol_diff_4h,
            "positive_chunks_1h": pos_1h,
            "positive_chunks_4h": pos_4h,
        },
        "final_decision": final_decision,
    }


def render_candidate_alpha_semantic_markdown(memo: dict[str, Any]) -> str:
    interp = memo["interpretation"]
    lines = [
        "# Candidate Alpha Semantic Fix And Robustness Memo",
        "",
        "## Full Sample",
        f"- avoidance_minus_tradable_forward_return_1h: {interp['full_sample_avoidance_minus_tradable_1h']}",
        f"- avoidance_minus_tradable_forward_return_4h: {interp['full_sample_avoidance_minus_tradable_4h']}",
        f"- avoidance_minus_tradable_forward_vol_4h: {interp['full_sample_avoidance_minus_tradable_vol_4h']}",
        "",
        "## Subperiod Robustness",
    ]
    for label, comparison in memo["subperiods"].items():
        diff = comparison["diff_avoidance_minus_tradable"]
        lines.extend(
            [
                f"### {label}",
                f"- forward_return_1h diff: {diff['forward_return_1h']}",
                f"- forward_return_4h diff: {diff['forward_return_4h']}",
                f"- forward_vol_4h diff: {diff['forward_vol_4h']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Decision",
            f"- likely_real_signal: {interp['likely_real_signal']}",
            f"- invert_label_semantics: {interp['invert_label_semantics']}",
            f"- final_decision: {memo['final_decision']}",
        ]
    )
    return "\n".join(lines) + "\n"


def run_candidate_alpha_semantic_fix(analysis_dir: Path, *, frame_path: Path | None = None) -> CandidateAlphaSemanticArtifacts:
    selected_frame_path = frame_path or _latest_analysis_frame(analysis_dir)
    frame = load_candidate_alpha_frame(selected_frame_path)
    memo = build_candidate_alpha_semantic_memo(frame)

    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    memo_json_path = analysis_dir / f"candidate_alpha_semantic_fix_{stamp}.json"
    memo_md_path = analysis_dir / f"candidate_alpha_semantic_fix_{stamp}.md"
    memo_json_path.write_text(json.dumps(memo, indent=2), encoding="utf-8")
    memo_md_path.write_text(render_candidate_alpha_semantic_markdown(memo), encoding="utf-8")
    return CandidateAlphaSemanticArtifacts(memo_json_path=memo_json_path, memo_md_path=memo_md_path, memo=memo)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the Candidate Alpha semantic fix and robustness memo.")
    parser.add_argument("--analysis-dir", default="analysis_results")
    parser.add_argument("--frame-path", default=None)
    args = parser.parse_args()

    artifacts = run_candidate_alpha_semantic_fix(
        Path(args.analysis_dir),
        frame_path=Path(args.frame_path) if args.frame_path else None,
    )
    print(
        json.dumps(
            {
                "memo_json_path": str(artifacts.memo_json_path),
                "memo_md_path": str(artifacts.memo_md_path),
                "final_decision": artifacts.memo["final_decision"],
                "interpretation": artifacts.memo["interpretation"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
