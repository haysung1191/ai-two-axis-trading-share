from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_cand022_operator_decision_packet.py")
SPEC = importlib.util.spec_from_file_location("build_cand022_operator_decision_packet", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
packet_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(packet_mod)


class Cand022OperatorDecisionPacketTests(unittest.TestCase):
    def test_packet_is_review_only_and_preserves_safety(self) -> None:
        packet = packet_mod.build_packet("2026-05-14T05:00:00+09:00", {"decision": "BLOCK"})

        self.assertEqual(packet["current_decision"], "BLOCK")
        self.assertFalse(packet["tiny_live_ready"])
        self.assertTrue(packet["do_not_auto_apply"])
        self.assertEqual(packet["safety"], packet_mod.SAFETY)
        self.assertFalse(packet["safety"]["paper_enabled"])
        self.assertFalse(packet["safety"]["live_enabled"])
        self.assertFalse(packet["safety"]["broker_submit_allowed"])
        self.assertFalse(packet["safety"]["order_intent_created"])
        self.assertIn("do_not_enable_live", packet["forbidden_actions"])
        self.assertIn("do_not_modify_human_mandate_without_explicit_user_instruction", packet["forbidden_actions"])

    def test_shadow_only_exception_is_explicit_operator_choice_not_auto_transition(self) -> None:
        packet = packet_mod.build_packet("2026-05-14T05:00:00+09:00", {"decision": "BLOCK"})
        groups = {group["group_id"]: group for group in packet["decision_groups"]}
        data_policy = groups["kis_pit_survivorship_policy"]

        choices = {choice["choice_id"]: choice for choice in data_policy["operator_choices"]}
        self.assertIn("data_upgrade_required", choices)
        self.assertIn("shadow_only_exception", choices)
        self.assertIn("no-submit shadow observation", choices["shadow_only_exception"]["effect"])
        self.assertIn("still block paper/live/order intents", choices["shadow_only_exception"]["effect"])
        self.assertIn("Without a policy choice", data_policy["operator_action_needed"])
        self.assertIn("Stage 5 to Stage 6 transition must remain blocked", data_policy["operator_action_needed"])

    def test_human_mandate_completion_fields_are_decision_inputs_not_approval(self) -> None:
        packet = packet_mod.build_packet("2026-05-14T05:00:00+09:00", {"decision": "BLOCK"})
        groups = {group["group_id"]: group for group in packet["decision_groups"]}
        mandate = groups["human_mandate_completion"]

        self.assertIn("reporting_policy.checkpoint_email_frequency_hours", mandate["required_fields"])
        self.assertIn("incident_policy_confirmed.max_unreviewed_incident_age_hours", mandate["required_fields"])
        self.assertEqual(mandate["recommended_safe_values_for_review_only"]["reporting_policy"]["checkpoint_email_frequency_hours"], 3)
        self.assertFalse(
            mandate["recommended_safe_values_for_review_only"]["reporting_policy"][
                "unattended_codex_continuation_allowed"
            ]
        )
        self.assertIn("not approval", mandate["operator_action_needed"])
        self.assertIn("not a live authorization", mandate["operator_action_needed"])

    def test_markdown_surfaces_review_only_and_forbidden_actions(self) -> None:
        packet = packet_mod.build_packet("2026-05-14T05:00:00+09:00", {"decision": "BLOCK"})
        md = packet_mod.render_md(packet)

        self.assertIn("This packet enables trading: `false`", md)
        self.assertIn("This packet is approval: `false`", md)
        self.assertIn("Auto-apply allowed: `false`", md)
        self.assertIn("shadow_only_exception", md)
        self.assertIn("still block paper/live/order intents", md)
        self.assertIn("do_not_create_order_intent_from_this_packet", md)
        self.assertIn("do_not_enable_paper", md)
        self.assertIn("do_not_enable_live", md)
        self.assertIn("do_not_enable_broker_submit", md)
        self.assertIn('"pretrade_firewall_default_decision": "BLOCK"', md)


if __name__ == "__main__":
    unittest.main()
