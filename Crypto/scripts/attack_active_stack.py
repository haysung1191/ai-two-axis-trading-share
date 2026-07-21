from __future__ import annotations

ACTIVE_ATTACK_MAIN_LABEL = "ratio112_tighter_stop_main"
ACTIVE_ATTACK_BACKUP_LABEL = "bridge_28_relief"
ACTIVE_ATTACK_CHALLENGER_LABEL = "post_spike_trend960_depth055_volume100_hold36"

ACTIVE_ATTACK_STACK_STATUS = {
    "attack_main": ACTIVE_ATTACK_MAIN_LABEL,
    "attack_backup": ACTIVE_ATTACK_BACKUP_LABEL,
    "attack_challenger": ACTIVE_ATTACK_CHALLENGER_LABEL,
}

ACTIVE_ATTACK_STACK_DECISION = (
    "The exact-hit frontier bridge candidate bridge_28_relief closes the promoted-backup 20bps gap while keeping "
    "drift inside the guardrail, so it takes the active attack backup lane while "
    "trend960_depth055_volume100_hold36 is now the active post-spike challenger after the approved rotation."
)
