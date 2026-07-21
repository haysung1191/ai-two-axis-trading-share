from __future__ import annotations

import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


CURRENT_STATE_JSON = REPO_ROOT / "output" / "split_models_operational_conversion_current_state.json"
OUTPUT_DIR = REPO_ROOT / "output" / "split_models_operational_conversion_dashboard"
OUTPUT_HTML = OUTPUT_DIR / "dashboard.html"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _status_color(gate_status: str) -> str:
    if gate_status.upper() == "OPEN":
        return "#1f7a4c"
    if gate_status.upper() == "BLOCKED":
        return "#9d2b2b"
    return "#8a6d1d"


def _card(title: str, value: str) -> str:
    return (
        "<div class='card'>"
        f"<div class='label'>{title}</div>"
        f"<div class='value'>{value}</div>"
        "</div>"
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    current_state = _load_json(CURRENT_STATE_JSON)
    accent = _status_color(str(current_state["gate_status"]))
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Operational Conversion Dashboard</title>
  <style>
    :root {{
      --accent: {accent};
      --bg1: #f7f1e8;
      --bg2: #eef3fb;
      --ink: #1f2430;
      --muted: #5f6673;
      --panel: rgba(255,255,255,0.86);
      --border: rgba(20,20,20,0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", "Apple SD Gothic Neo", sans-serif;
      color: var(--ink);
      background: linear-gradient(180deg, var(--bg1), var(--bg2));
    }}
    .wrap {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 32px 20px 56px;
    }}
    .hero {{
      background: linear-gradient(135deg, rgba(255,255,255,0.92), rgba(255,255,255,0.7));
      border: 1px solid var(--border);
      border-radius: 24px;
      padding: 28px;
      box-shadow: 0 18px 50px rgba(40, 48, 71, 0.08);
    }}
    .eyebrow {{
      color: var(--muted);
      font-size: 14px;
      margin-bottom: 10px;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 36px;
    }}
    .subtitle {{
      color: var(--muted);
      line-height: 1.6;
      max-width: 760px;
    }}
    .pills {{
      margin-top: 18px;
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }}
    .pill {{
      padding: 10px 14px;
      border-radius: 999px;
      color: white;
      font-weight: 700;
    }}
    .pill.blue {{ background: #3b5b92; }}
    .pill.brown {{ background: #5d4037; }}
    .metrics {{
      margin-top: 22px;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 14px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 16px;
    }}
    .label {{
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 8px;
    }}
    .value {{
      font-size: 24px;
      font-weight: 700;
      line-height: 1.25;
      word-break: break-word;
    }}
    .grid {{
      margin-top: 18px;
      display: grid;
      grid-template-columns: 1.2fr 0.9fr;
      gap: 18px;
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: 20px;
    }}
    h2 {{
      margin-top: 0;
      font-size: 22px;
    }}
    ul {{
      margin: 0;
      padding-left: 18px;
      line-height: 1.7;
    }}
    code, pre {{
      font-family: Consolas, monospace;
    }}
    .cmd {{
      background: #101522;
      color: #edf2ff;
      border-radius: 14px;
      padding: 12px 14px;
      margin: 10px 0;
      overflow-x: auto;
    }}
    .small {{
      color: var(--muted);
      font-size: 14px;
    }}
    @media (max-width: 900px) {{
      .grid {{ grid-template-columns: 1fr; }}
      h1 {{ font-size: 30px; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <div class="eyebrow">Split Models Operational Conversion Branch</div>
      <h1>One-Page Dashboard</h1>
      <div class="subtitle">
        This branch is blocked from operating promotion. Anchor drawdown is still worse than the baseline,
        but the branch now has {current_state['drawdown_improver_count']} drawdown-improving axis/axes.
      </div>
      <div class="pills">
        <div class="pill" style="background:{accent}">Gate: {current_state['gate_status']}</div>
        <div class="pill blue">Promotion: {current_state['promotion_status']}</div>
        <div class="pill brown">Anchor: {current_state['anchor_variant']}</div>
      </div>
      <div class="metrics">
        {_card("Anchor MDD", current_state["anchor_mdd_display"])}
        {_card("Baseline MDD", current_state["baseline_mdd_display"])}
        {_card("Drawdown Gap", current_state["drawdown_gap_vs_baseline_display"])}
        {_card("Best Quality Overlay", current_state["best_quality_variant"])}
        {_card("Representative Candidate", current_state["recommended_representative_variant"])}
        {_card("Live Execution Mode", current_state["recommended_live_execution_mode"])}
        {_card("Challenger Search Closed", str(current_state["representative_challenger_search_closed"]))}
        {_card("Challenger Families", str(current_state["challenger_family_count"]))}
        {_card("Drawdown Improvers", str(current_state["drawdown_improver_count"]))}
        {_card("Quality Overlays", str(current_state["quality_overlay_count"]))}
        {_card("No-op Axes", str(current_state["no_op_count"]))}
      </div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>Simple Reading</h2>
        <ul>
          <li>Current gate status is <code>{current_state['gate_status']}</code>.</li>
          <li>The direct block reason is <code>{current_state['promotion_status']}</code>.</li>
          <li>The best current anchor is <code>{current_state['anchor_variant']}</code>.</li>
          <li>The official representative candidate is <code>{current_state['recommended_representative_variant']}</code>.</li>
          <li>The recent representative challenger search is closed with <code>{current_state['challenger_family_count']}</code> tested families and <code>{current_state['representative_replacements_found']}</code> replacements.</li>
          <li>Closure verdict: <code>{current_state['representative_challenger_closure_verdict']}</code>.</li>
          <li>Representative decision: <code>{current_state['representative_decision_verdict']}</code>.</li>
          <li>Probe contract: <code>{current_state['probe_contract_verdict']}</code>.</li>
          <li>Refresh contract: <code>{current_state['refresh_contract_verdict']}</code>.</li>
          <li>Entrypoint contract: <code>{current_state['entrypoint_contract_verdict']}</code>.</li>
          <li>Live execution mode: <code>{current_state['recommended_live_execution_mode']}</code>.</li>
          <li>Execution gate verdict: <code>{current_state['execution_gate_verdict']}</code>.</li>
          <li>Drawdown-improving axes now exist, but the branch is still below the operating baseline bar.</li>
          <li>This branch stays closed until a genuinely better structure appears.</li>
        </ul>
      </div>
      <div class="panel">
        <h2>Verification</h2>
        <ul>
          <li>Doctor smoke: <code>{current_state['doctor_smoke_test_status']}</code></li>
          <li>Doctor smoke return codes: <code>{current_state['doctor_smoke_process_a']}</code>,
              <code>{current_state['doctor_smoke_process_b']}</code></li>
          <li>Doctor lock event sequence: <code>{', '.join(current_state['doctor_lock_event_sequence'])}</code></li>
          <li>Probe smoke: <code>{current_state['probe_smoke_test_status']}</code></li>
          <li>Probe exit codes: python <code>{current_state['python_probe_exit_code']}</code>,
              powershell <code>{current_state['powershell_probe_exit_code']}</code>,
              cmd <code>{current_state['cmd_probe_exit_code']}</code></li>
          <li>Stale lock smoke: <code>{current_state['stale_lock_smoke_test_status']}</code></li>
          <li>Stale lock sync stdout: <code>{current_state['stale_lock_sync_stdout']}</code></li>
          <li>Lock dir exists after stale-lock sync: <code>{current_state['stale_lock_dir_exists_after_sync']}</code></li>
        </ul>
      </div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>Commands To Use</h2>
        <div class="cmd">{current_state['primary_human_command']}</div>
        <div class="cmd">{current_state['gate_probe_command']}</div>
        <div class="cmd">python tools/analysis/check_split_models_operational_conversion_state.py</div>
      </div>
      <div class="panel">
        <h2>File To Read</h2>
        <div class="cmd">{current_state['primary_read_file']}</div>
        <div class="small">
          Humans should run launch. Processes should call probe. If you need one source of truth,
          read current_state.json. The local dashboard file is shown below.
        </div>
        <div class="cmd">{current_state['dashboard_file']}</div>
        <div class="cmd">{current_state['representative_challenger_closure_file']}</div>
        <div class="cmd">{current_state['representative_decision_file']}</div>
        <div class="cmd">{current_state['probe_contract_file']}</div>
        <div class="cmd">{current_state['refresh_contract_file']}</div>
        <div class="cmd">{current_state['entrypoint_contract_file']}</div>
      </div>
    </section>
  </div>
</body>
</html>
"""

    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(json.dumps({"dashboard_html": str(OUTPUT_HTML.relative_to(REPO_ROOT))}, indent=2))


if __name__ == "__main__":
    main()
