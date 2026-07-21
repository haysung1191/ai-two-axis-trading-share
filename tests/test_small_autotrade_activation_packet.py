from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_small_autotrade_activation_packet.py")
SPEC = importlib.util.spec_from_file_location("build_small_autotrade_activation_packet", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
activation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(activation)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


class SmallAutotradeActivationPacketTests(unittest.TestCase):
    def test_activation_blocks_until_paper_promotion_evidence_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            activation.RISK_BUDGET = root / "risk_budget.json"
            activation.BRIDGE_GATE = root / "bridge_gate.json"
            activation.SHADOW_HEALTH = root / "shadow_health.json"
            activation.SHADOW_CONTROL = root / "shadow_control.json"
            activation.PAPER_SIM = root / "paper_sim.json"
            activation.PAPER_PROMOTION_EVIDENCE = root / "paper_promotion.json"
            activation.KILL_SWITCH = root / "kill_switch.json"
            activation.GLOBAL_DISABLE = root / "DISABLE_ALL_TRADING"

            activation.GLOBAL_DISABLE.write_text("disabled", encoding="utf-8")
            write_json(
                activation.RISK_BUDGET,
                {
                    "strategies": [
                        {
                            "name": "small_account_growth_paper",
                            "cash_weight": 0.55,
                            "total_model_weight": 0.45,
                            "sleeves": [],
                        }
                    ]
                },
            )
            write_json(activation.BRIDGE_GATE, {"gate_summary": {"usable_now": True}})
            write_json(
                activation.SHADOW_HEALTH,
                {"health": "green", "unexpected_failure_count": 0, "paper_eligibility": {"eligible": True}},
            )
            write_json(
                activation.SHADOW_CONTROL,
                {"contract_count": 1, "planned_count": 1, "include_pending_validation": False},
            )
            write_json(activation.PAPER_SIM, {"status": "pass", "real_orders": 0, "private_submit_used": False})
            write_json(activation.KILL_SWITCH, {"paper_enabled": False, "live_enabled": False})
            write_json(
                activation.PAPER_PROMOTION_EVIDENCE,
                {
                    "decision": "KEEP_PAPER_COLLECT_EVIDENCE",
                    "evidence_gaps": ["INSUFFICIENT_PAPER_CYCLES"],
                    "evidence": {
                        "paper_cycles_completed": 250,
                        "evidence_deficit": {"paper_loop_cycles_missing": 38},
                    },
                },
            )

            packet = activation.build_packet()

        self.assertEqual(packet["status"], "blocked")
        self.assertIn("paper_promotion_evidence_not_ready", packet["blockers"])
        self.assertIn("paper_promotion_evidence_has_gaps", packet["blockers"])
        self.assertEqual(packet["paper_promotion_evidence"]["paper_loop_cycles_missing"], 38)
        self.assertFalse(packet["does_enable_trading"])
        self.assertFalse(packet["broker_submit_allowed"])

    def test_activation_ready_when_paper_promotion_evidence_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            activation.RISK_BUDGET = root / "risk_budget.json"
            activation.BRIDGE_GATE = root / "bridge_gate.json"
            activation.SHADOW_HEALTH = root / "shadow_health.json"
            activation.SHADOW_CONTROL = root / "shadow_control.json"
            activation.PAPER_SIM = root / "paper_sim.json"
            activation.PAPER_PROMOTION_EVIDENCE = root / "paper_promotion.json"
            activation.KILL_SWITCH = root / "kill_switch.json"
            activation.GLOBAL_DISABLE = root / "DISABLE_ALL_TRADING"

            activation.GLOBAL_DISABLE.write_text("disabled", encoding="utf-8")
            write_json(
                activation.RISK_BUDGET,
                {"strategies": [{"name": "small_account_growth_paper", "sleeves": []}]},
            )
            write_json(activation.BRIDGE_GATE, {"gate_summary": {"usable_now": True}})
            write_json(
                activation.SHADOW_HEALTH,
                {"health": "green", "unexpected_failure_count": 0, "paper_eligibility": {"eligible": True}},
            )
            write_json(
                activation.SHADOW_CONTROL,
                {"contract_count": 1, "planned_count": 1, "include_pending_validation": False},
            )
            write_json(activation.PAPER_SIM, {"status": "pass", "real_orders": 0, "private_submit_used": False})
            write_json(activation.KILL_SWITCH, {"paper_enabled": False, "live_enabled": False})
            write_json(
                activation.PAPER_PROMOTION_EVIDENCE,
                {"decision": "PROMOTION_REVIEW_READY", "evidence_gaps": [], "evidence": {}},
            )

            packet = activation.build_packet()

        self.assertEqual(packet["status"], "ready_for_explicit_paper_activation")
        self.assertEqual(packet["blockers"], [])


if __name__ == "__main__":
    unittest.main()
