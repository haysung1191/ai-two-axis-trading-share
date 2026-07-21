from __future__ import annotations

import json
from pathlib import Path

import streamlit as st


REPO_ROOT = Path(__file__).resolve().parents[2]
CURRENT_STATE_JSON = REPO_ROOT / "output" / "split_models_operational_conversion_current_state.json"
MANIFEST_JSON = REPO_ROOT / "output" / "split_models_operational_conversion_manifest.json"
HANDOFF_JSON = REPO_ROOT / "output" / "split_models_operational_conversion_handoff" / "handoff_summary.json"


@st.cache_data(ttl=300)
def _load_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def main() -> None:
    st.set_page_config(
        page_title="Operational Conversion Branch",
        page_icon="P",
        layout="wide",
    )

    current_state = _load_json(CURRENT_STATE_JSON)
    manifest = _load_json(MANIFEST_JSON)
    handoff = _load_json(HANDOFF_JSON)

    st.title("Split Models Operational Conversion")
    st.caption("Remote dashboard for the current operational-conversion branch")

    if any(item is None for item in [current_state, manifest, handoff]):
        st.error("Required state files could not be loaded.")
        st.code(str(CURRENT_STATE_JSON), language="text")
        st.code(str(MANIFEST_JSON), language="text")
        st.code(str(HANDOFF_JSON), language="text")
        st.stop()

    gate_status = str(current_state["gate_status"])
    promotion_status = str(current_state["promotion_status"])
    accent = {"OPEN": "green", "BLOCKED": "red"}.get(gate_status, "orange")

    st.markdown(f"### Status: :{accent}[**{gate_status}**] / `{promotion_status}`")
    st.write(
        "Simple reading: this candidate is not discarded, but it is not safe enough for operating use yet "
        "because the downside drawdown is still too deep."
    )

    top = st.columns(4)
    top[0].metric("Anchor", handoff["anchor_variant"])
    top[1].metric("Anchor MDD", handoff["anchor_mdd_display"])
    top[2].metric("Baseline MDD", handoff["baseline_mdd_display"])
    top[3].metric("Drawdown Gap", handoff["drawdown_gap_vs_baseline_display"])

    counts = st.columns(3)
    counts[0].metric("Drawdown Improvers", int(current_state["drawdown_improver_count"]))
    counts[1].metric("Quality Overlays", int(current_state["quality_overlay_count"]))
    counts[2].metric("No-op Axes", int(current_state["no_op_count"]))
    st.caption(
        f"Live execution mode: {current_state['recommended_live_execution_mode']} / "
        f"{current_state['execution_gate_verdict']}"
    )

    left, right = st.columns([1.15, 0.85], gap="large")

    with left:
        st.subheader("Bottom Line")
        st.markdown(
            "\n".join(
                [
                    "- Do not promote this branch to operating use now.",
                    "- The direct reason is worse drawdown than the baseline.",
                    f"- Current live execution mode: `{current_state['recommended_live_execution_mode']}`.",
                    "- Keep it closed until a new structure really fixes that drawdown problem.",
                ]
            )
        )

        st.subheader("What to Use")
        st.code(manifest["doctor_command"], language="bash")
        st.code(manifest["gate_probe_command"], language="bash")
        st.code(manifest["primary_read_file"], language="text")

    with right:
        st.subheader("Verification")
        verify = st.columns(3)
        verify[0].metric("Doctor Smoke", current_state["doctor_smoke_test_status"])
        verify[1].metric("Probe Smoke", current_state["probe_smoke_test_status"])
        verify[2].metric("Stale Lock Smoke", current_state["stale_lock_smoke_test_status"])
        st.caption(
            f"Doctor smoke return codes: {current_state['doctor_smoke_process_a']}, "
            f"{current_state['doctor_smoke_process_b']}"
        )
        st.caption(
            "Doctor lock event sequence: "
            + ", ".join(current_state["doctor_lock_event_sequence"])
        )
        exits = st.columns(3)
        exits[0].metric("Py Probe", str(current_state["python_probe_exit_code"]))
        exits[1].metric("PS Probe", str(current_state["powershell_probe_exit_code"]))
        exits[2].metric("CMD Probe", str(current_state["cmd_probe_exit_code"]))
        st.caption(
            f"Stale lock sync stdout: {current_state['stale_lock_sync_stdout']} / "
            f"lock dir remains: {current_state['stale_lock_dir_exists_after_sync']}"
        )

    with st.expander("Raw JSON"):
        st.json(
            {
                "current_state": current_state,
                "manifest": manifest,
                "handoff": handoff,
            }
        )


if __name__ == "__main__":
    main()
