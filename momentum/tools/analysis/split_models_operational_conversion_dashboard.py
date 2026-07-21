from __future__ import annotations

import json
from pathlib import Path
import sys

import streamlit as st


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


CURRENT_STATE_JSON = REPO_ROOT / "output" / "split_models_operational_conversion_current_state.json"
MANIFEST_JSON = REPO_ROOT / "output" / "split_models_operational_conversion_manifest.json"
HANDOFF_JSON = REPO_ROOT / "output" / "split_models_operational_conversion_handoff" / "handoff_summary.json"
CHECK_SCRIPT = "python tools/analysis/check_split_models_operational_conversion_state.py"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _status_color(gate_status: str) -> str:
    if gate_status.upper() == "OPEN":
        return "#1f7a4c"
    if gate_status.upper() == "BLOCKED":
        return "#9d2b2b"
    return "#8a6d1d"


def _pill(label: str, value: str, *, color: str) -> str:
    return (
        f"<div style='padding:10px 14px;border-radius:14px;background:{color};"
        "color:white;font-weight:700;display:inline-block;margin-right:8px;'>"
        f"{label}: {value}</div>"
    )


def main() -> None:
    current_state = _load_json(CURRENT_STATE_JSON)
    manifest = _load_json(MANIFEST_JSON)
    handoff = _load_json(HANDOFF_JSON)

    st.set_page_config(
        page_title="Operational Conversion Dashboard",
        page_icon="OC",
        layout="wide",
    )

    accent = _status_color(str(current_state["gate_status"]))
    st.markdown(
        """
        <style>
        .main {
            background: linear-gradient(180deg, #f7f1e8 0%, #f4f6fb 100%);
        }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        div[data-testid="stMetric"] {
            background: rgba(255,255,255,0.82);
            border: 1px solid rgba(20,20,20,0.08);
            padding: 0.8rem 1rem;
            border-radius: 16px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("Split Models Operational Conversion Dashboard")
    st.caption("Single-thread operating view for the current operational-conversion branch.")

    st.markdown(
        _pill("Gate", str(current_state["gate_status"]), color=accent)
        + _pill("Promotion", str(current_state["promotion_status"]), color="#3b5b92")
        + _pill("Anchor", str(current_state["anchor_variant"]), color="#5d4037"),
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.3, 1.0], gap="large")

    with left:
        st.subheader("Quick Summary")
        st.write(
            "This branch is still blocked for operating promotion. "
            "The direct reason is that anchor drawdown remains worse than the baseline, "
            "even though several recent axes improved drawdown relative to the anchor."
        )

        metric_cols = st.columns(4)
        metric_cols[0].metric("Anchor MDD", handoff["anchor_mdd_display"])
        metric_cols[1].metric("Baseline MDD", handoff["baseline_mdd_display"])
        metric_cols[2].metric("Drawdown Gap", handoff["drawdown_gap_vs_baseline_display"])
        metric_cols[3].metric("Best Quality Overlay", handoff["best_quality_variant"])

        count_cols = st.columns(3)
        count_cols[0].metric("Drawdown Improvers", int(current_state["drawdown_improver_count"]))
        count_cols[1].metric("Quality Overlays", int(current_state["quality_overlay_count"]))
        count_cols[2].metric("No-op Axes", int(current_state["no_op_count"]))
        st.caption(
            f"Live execution mode: {current_state['recommended_live_execution_mode']} / "
            f"{current_state['execution_gate_verdict']}"
        )

        st.subheader("What To Read Right Now")
        st.code(manifest["doctor_command"], language="bash")
        st.code(manifest["gate_probe_command"], language="bash")
        st.code(manifest["primary_read_file"], language="text")

    with right:
        st.subheader("Decision Read")
        st.markdown(
            f"""
            - Current gate: `{current_state['gate_status']}`
            - Current promotion status: `{current_state['promotion_status']}`
            - Current anchor: `{current_state['anchor_variant']}`
            - Live execution mode: `{current_state['recommended_live_execution_mode']}`
            - Humans should use `doctor`
            - Processes should use `probe`
            """
        )

        st.subheader("Verification Status")
        verification_cols = st.columns(3)
        verification_cols[0].metric("Doctor Smoke", current_state["doctor_smoke_test_status"])
        verification_cols[1].metric("Probe Smoke", current_state["probe_smoke_test_status"])
        verification_cols[2].metric("Stale Lock Smoke", current_state["stale_lock_smoke_test_status"])
        st.caption(
            f"Doctor smoke return codes: {current_state['doctor_smoke_process_a']}, "
            f"{current_state['doctor_smoke_process_b']}"
        )
        st.caption(
            "Doctor lock event sequence: "
            + ", ".join(current_state["doctor_lock_event_sequence"])
        )
        st.caption(
            f"Probe exit codes: python {current_state['python_probe_exit_code']}, "
            f"powershell {current_state['powershell_probe_exit_code']}, "
            f"cmd {current_state['cmd_probe_exit_code']}"
        )
        st.caption(
            f"Stale lock sync stdout: {current_state['stale_lock_sync_stdout']} / "
            f"lock dir remains: {current_state['stale_lock_dir_exists_after_sync']}"
        )
        st.caption(f"Consistency check command: {CHECK_SCRIPT}")

    tab_summary, tab_files, tab_raw = st.tabs(["Simple Read", "File Paths", "Raw JSON"])

    with tab_summary:
        st.markdown(
            """
            ### Plain-English Read

            - This branch is still blocked.
            - The best nearby candidate improved the anchor, but drawdown is still worse than the operating baseline.
            - Some overlays improved quality or local drawdown shape, but none repaired the operating drawdown gap enough.
            - Keep the branch closed until a genuinely better structure appears.
            """
        )

    with tab_files:
        st.markdown("### Canonical Files")
        file_rows = [
            ("Current State", "output/split_models_operational_conversion_current_state.json"),
            ("Manifest", "output/split_models_operational_conversion_manifest.json"),
            ("Handoff", "output/split_models_operational_conversion_handoff/handoff_summary.json"),
            ("Closure", "output/split_models_operational_conversion_closure/closure_summary.json"),
            ("Check Command", CHECK_SCRIPT),
        ]
        for label, value in file_rows:
            st.write(f"- **{label}**: `{value}`")

    with tab_raw:
        raw_left, raw_right = st.columns(2)
        raw_left.json(current_state)
        raw_right.json(
            {
                "manifest": manifest,
                "handoff": handoff,
            }
        )


if __name__ == "__main__":
    main()
