from __future__ import annotations

FAST_GATE_SHARED_HANDOFF_KEYS = [
    "attack_challenger_remote_monitoring_deployment_handoff_ready",
    "attack_challenger_next_step",
    "attack_challenger_bridge_report",
    "deployment_monitoring_active",
]

FAST_GATE_SHARED_HANDOFF_KEYS_WITH_BRIEF_MIRRORS = [
    *FAST_GATE_SHARED_HANDOFF_KEYS,
    "operating_brief_attack_challenger_remote_monitoring_deployment_handoff_ready",
    "operating_brief_attack_challenger_next_step",
    "operating_brief_attack_challenger_bridge_report",
    "operating_brief_deployment_monitoring_active",
]
