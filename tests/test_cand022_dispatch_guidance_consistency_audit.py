from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_cand022_dispatch_guidance_consistency_audit.py")
SPEC = importlib.util.spec_from_file_location("build_cand022_dispatch_guidance_consistency_audit", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
audit_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit_mod)


class Cand022DispatchGuidanceConsistencyAuditTests(unittest.TestCase):
    def test_audit_passes_when_all_targets_are_helper_first(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            targets = {}
            for name in ("a.md", "b.json", "c.md"):
                path = root / name
                path.write_text(
                    "Run python .\\write_cand022_dispatch_sent_confirmation.py --i-confirm-actual-send after actual send. "
                    "Then run python .\\run_cand022_provider_return_watch.py --cycles 180. "
                    "Run python .\\build_kis_provider_returned_to_handoff_copy_review.py and review "
                    "kis_provider_returned_to_handoff_copy_review_latest.json before refresh. "
                    "Refresh is allowed only after READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW "
                    "and forbidden while BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW.",
                    encoding="utf-8",
                )
                targets[name] = path

            report = audit_mod.build_report("2026-05-14T06:00:00+09:00", targets=targets)

        self.assertEqual(report["status"], "PASS_DISPATCH_GUIDANCE_HELPER_FIRST")
        self.assertEqual(report["blockers"], [])
        self.assertFalse(report["safety"]["order_intent_created"])
        self.assertIn("does_not_send_email", report["non_goals"])

        md = audit_mod.render_md(report)
        self.assertIn("PASS_DISPATCH_GUIDANCE_HELPER_FIRST", md)
        self.assertIn("write_cand022_dispatch_sent_confirmation.py", md)

    def test_default_targets_include_human_facing_operator_status_brief_markdown(self) -> None:
        self.assertIn("next_action_router_md", audit_mod.DEFAULT_TARGETS)
        self.assertIn("start_here_after_reboot_md", audit_mod.DEFAULT_TARGETS)
        self.assertIn("pipeline_restart_handoff_md", audit_mod.DEFAULT_TARGETS)
        self.assertIn("start_here_after_reboot_md", audit_mod.DURABLE_RESTART_TARGETS)
        self.assertIn("pipeline_restart_handoff_md", audit_mod.DURABLE_RESTART_TARGETS)
        self.assertIn("provider_return_watcher_pids:", audit_mod.DURABLE_RESTART_WATCHER_TOKENS)
        self.assertIn("provider_return_watcher_max_remaining_minutes:", audit_mod.DURABLE_RESTART_WATCHER_TOKENS)
        self.assertIn("operator_status_brief_json", audit_mod.DEFAULT_TARGETS)
        self.assertIn("operator_status_brief_md", audit_mod.DEFAULT_TARGETS)
        self.assertTrue(str(audit_mod.DEFAULT_TARGETS["operator_status_brief_md"]).endswith("CAND-022_operator_status_brief.latest.md"))
        self.assertIn("stage6_user_action_card_json", audit_mod.DEFAULT_TARGETS)
        self.assertIn("stage6_user_action_card_md", audit_mod.DEFAULT_TARGETS)
        self.assertIn("stage6_two_path_decision_slip_json", audit_mod.DEFAULT_TARGETS)
        self.assertIn("stage6_two_path_decision_slip_md", audit_mod.DEFAULT_TARGETS)
        self.assertTrue(
            str(audit_mod.DEFAULT_TARGETS["stage6_user_action_card_md"]).endswith(
                "CAND-022_stage6_user_action_card.latest.md"
            )
        )
        self.assertIn("returned_staging_readme_md", audit_mod.DEFAULT_TARGETS)
        self.assertTrue(
            str(audit_mod.DEFAULT_TARGETS["returned_staging_readme_md"]).endswith(
                "provider_handoff\\returned\\CAND-022_latest\\README.md"
            )
        )
        self.assertIn("manual_dispatch_execution_slip_json", audit_mod.DEFAULT_TARGETS)
        self.assertIn("manual_dispatch_execution_slip_md", audit_mod.DEFAULT_TARGETS)
        self.assertIn("stage6_entry_path_audit_json", audit_mod.DEFAULT_TARGETS)
        self.assertIn("stage6_blocker_closure_plan_json", audit_mod.DEFAULT_TARGETS)
        self.assertIn("stage6_operator_wait_packet_json", audit_mod.DEFAULT_TARGETS)
        self.assertIn("blocked_wait_state_json", audit_mod.DEFAULT_TARGETS)
        self.assertIn("manual_dispatch_execution_slip_json", audit_mod.WATCH_REQUIRED_TARGETS)
        self.assertIn("stage6_user_action_card_json", audit_mod.WATCH_REQUIRED_TARGETS)
        self.assertIn("stage6_user_action_card_md", audit_mod.WATCH_REQUIRED_TARGETS)
        self.assertIn("stage6_two_path_decision_slip_json", audit_mod.WATCH_REQUIRED_TARGETS)
        self.assertIn("stage6_two_path_decision_slip_md", audit_mod.WATCH_REQUIRED_TARGETS)
        self.assertIn("stage6_entry_path_audit_json", audit_mod.WATCH_REQUIRED_TARGETS)
        self.assertIn("stage6_blocker_closure_plan_json", audit_mod.WATCH_REQUIRED_TARGETS)
        self.assertIn("next_action_router_json", audit_mod.COPY_REVIEW_REQUIRED_TARGETS)
        self.assertIn("operator_status_brief_md", audit_mod.COPY_REVIEW_REQUIRED_TARGETS)
        self.assertIn("stage6_user_action_card_json", audit_mod.COPY_REVIEW_REQUIRED_TARGETS)
        self.assertIn("stage6_user_action_card_md", audit_mod.COPY_REVIEW_REQUIRED_TARGETS)
        self.assertIn("stage6_two_path_decision_slip_json", audit_mod.COPY_REVIEW_REQUIRED_TARGETS)
        self.assertIn("stage6_two_path_decision_slip_md", audit_mod.COPY_REVIEW_REQUIRED_TARGETS)
        self.assertIn("returned_staging_readme_md", audit_mod.COPY_REVIEW_REQUIRED_TARGETS)
        self.assertIn("stage6_operator_wait_packet_json", audit_mod.COPY_REVIEW_REQUIRED_TARGETS)
        self.assertIn("blocked_wait_state_json", audit_mod.COPY_REVIEW_REQUIRED_TARGETS)
        self.assertEqual(
            audit_mod.COPY_REVIEW_READY_TOKEN,
            "READY_FOR_MANUAL_RETURNED_TO_HANDOFF_COPY_REVIEW",
        )
        self.assertEqual(audit_mod.COPY_REVIEW_BLOCK_TOKEN, "BLOCK_RETURNED_TO_HANDOFF_COPY_REVIEW")
        self.assertEqual(
            audit_mod.COPY_REVIEW_SCRIPT_TOKEN,
            "build_kis_provider_returned_to_handoff_copy_review.py",
        )
        self.assertTrue(
            str(audit_mod.DEFAULT_TARGETS["manual_dispatch_execution_slip_md"]).endswith(
                "CAND-022_manual_dispatch_execution_slip.latest.md"
            )
        )

    def test_audit_blocks_stale_manual_confirmation_wording(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stale = root / "stale.md"
            stale.write_text(
                "Run python .\\write_cand022_dispatch_sent_confirmation.py --i-confirm-actual-send, "
                "but also fill dispatch confirmation manually.",
                encoding="utf-8",
            )

            report = audit_mod.build_report("2026-05-14T06:00:00+09:00", targets={"stale": stale})

        self.assertEqual(report["status"], "BLOCK_DISPATCH_GUIDANCE_INCONSISTENT")
        self.assertIn("stale:stale_phrase:fill dispatch confirmation", report["blockers"])

    def test_audit_blocks_missing_helper_or_confirm_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing = root / "missing.md"
            missing.write_text("Manual send instructions only.", encoding="utf-8")

            report = audit_mod.build_report("2026-05-14T06:00:00+09:00", targets={"missing": missing})

        self.assertEqual(report["status"], "BLOCK_DISPATCH_GUIDANCE_INCONSISTENT")
        self.assertIn("missing:helper_token_missing", report["blockers"])
        self.assertIn("missing:confirm_flag_missing", report["blockers"])

    def test_audit_blocks_missing_watch_token_on_required_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            required = root / "manual_slip.json"
            required.write_text(
                "Run python .\\write_cand022_dispatch_sent_confirmation.py --i-confirm-actual-send after actual send.",
                encoding="utf-8",
            )

            report = audit_mod.build_report(
                "2026-05-14T06:00:00+09:00",
                targets={"manual_dispatch_execution_slip_json": required},
            )

        self.assertEqual(report["status"], "BLOCK_DISPATCH_GUIDANCE_INCONSISTENT")
        self.assertIn("manual_dispatch_execution_slip_json:watch_token_missing", report["blockers"])

    def test_audit_blocks_missing_copy_review_token_on_required_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            required = root / "router.json"
            required.write_text(
                "Run python .\\write_cand022_dispatch_sent_confirmation.py --i-confirm-actual-send after actual send. "
                "Then run python .\\run_cand022_provider_return_watch.py --cycles 180.",
                encoding="utf-8",
            )

            report = audit_mod.build_report(
                "2026-05-14T06:00:00+09:00",
                targets={"next_action_router_json": required},
            )

        self.assertEqual(report["status"], "BLOCK_DISPATCH_GUIDANCE_INCONSISTENT")
        self.assertIn("next_action_router_json:copy_review_token_missing", report["blockers"])
        self.assertIn("next_action_router_json:copy_review_ready_token_missing", report["blockers"])
        self.assertIn("next_action_router_json:copy_review_block_token_missing", report["blockers"])
        self.assertIn("next_action_router_json:copy_review_script_token_missing", report["blockers"])

    def test_audit_blocks_weak_copy_review_contract_on_required_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            required = root / "stage6_card.md"
            required.write_text(
                "Run python .\\write_cand022_dispatch_sent_confirmation.py --i-confirm-actual-send after actual send. "
                "Then run python .\\run_cand022_provider_return_watch.py --cycles 180. "
                "Review kis_provider_returned_to_handoff_copy_review_latest.json before refresh.",
                encoding="utf-8",
            )

            report = audit_mod.build_report(
                "2026-05-14T06:00:00+09:00",
                targets={"stage6_user_action_card_md": required},
            )

        self.assertEqual(report["status"], "BLOCK_DISPATCH_GUIDANCE_INCONSISTENT")
        self.assertIn("stage6_user_action_card_md:copy_review_ready_token_missing", report["blockers"])
        self.assertIn("stage6_user_action_card_md:copy_review_block_token_missing", report["blockers"])
        self.assertIn("stage6_user_action_card_md:copy_review_script_token_missing", report["blockers"])

    def test_audit_requires_clean_korean_for_manual_dispatch_slip_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            slip = root / "manual_slip.md"
            slip.write_text(
                "Run python .\\write_cand022_dispatch_sent_confirmation.py --i-confirm-actual-send. "
                "Then run python .\\run_cand022_provider_return_watch.py --cycles 180. "
                "실제 발송 후에만 dry-run helper first.",
                encoding="utf-8",
            )

            report = audit_mod.build_report(
                "2026-05-14T06:00:00+09:00",
                targets={"manual_dispatch_execution_slip_md": slip},
            )

        self.assertEqual(report["status"], "PASS_DISPATCH_GUIDANCE_HELPER_FIRST")
        self.assertTrue(report["inspections"][0]["has_manual_slip_korean_token"])

    def test_audit_blocks_mojibake_for_manual_dispatch_slip_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            slip = root / "manual_slip.md"
            slip.write_text(
                "Run python .\\write_cand022_dispatch_sent_confirmation.py --i-confirm-actual-send. "
                "Then run python .\\run_cand022_provider_return_watch.py --cycles 180. "
                f"{audit_mod.MOJIBAKE_PHRASES[0]} helper text.",
                encoding="utf-8",
            )

            report = audit_mod.build_report(
                "2026-05-14T06:00:00+09:00",
                targets={"manual_dispatch_execution_slip_md": slip},
            )

        self.assertEqual(report["status"], "BLOCK_DISPATCH_GUIDANCE_INCONSISTENT")
        self.assertIn("manual_dispatch_execution_slip_md:manual_slip_korean_token_missing", report["blockers"])
        self.assertTrue(any("mojibake_phrase" in blocker for blocker in report["blockers"]))

    def test_audit_blocks_stale_reboot_handoff_single_watcher_pid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff = root / "START_HERE_AFTER_REBOOT.md"
            handoff.write_text(
                "Run python .\\write_cand022_dispatch_sent_confirmation.py --i-confirm-actual-send. "
                "Then run python .\\run_cand022_provider_return_watch.py --cycles 180. "
                "provider_return_watcher_pid: 5560\n"
                "provider_return_watcher_expected_end_kst: 2026-05-14T20:48:56+09:00\n",
                encoding="utf-8",
            )

            report = audit_mod.build_report(
                "2026-05-14T06:00:00+09:00",
                targets={"start_here_after_reboot_md": handoff},
            )

        self.assertEqual(report["status"], "BLOCK_DISPATCH_GUIDANCE_INCONSISTENT")
        self.assertIn("start_here_after_reboot_md:stale_phrase:provider_return_watcher_pid:", report["blockers"])
        self.assertIn(
            "start_here_after_reboot_md:durable_restart_token_missing:provider_return_watcher_pids:",
            report["blockers"],
        )


if __name__ == "__main__":
    unittest.main()
