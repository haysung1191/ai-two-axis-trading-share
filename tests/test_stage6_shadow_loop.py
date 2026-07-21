from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\run_stage6_shadow_loop.py")
SPEC = importlib.util.spec_from_file_location("run_stage6_shadow_loop", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
loop_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(loop_mod)


class Stage6ShadowLoopTests(unittest.TestCase):
    def test_cand022_signal_computation_uses_local_mapping_records_only(self) -> None:
        result = loop_mod.compute_cand022_signal("2026-05-14T09:00:00+09:00")

        self.assertTrue(result["ok"])
        self.assertEqual(result["symbol_count"], 7)
        self.assertEqual(result["source_mapping"], str(loop_mod.CAND022_MAPPING))
        self.assertEqual(result["source_current_signal_observation"], str(loop_mod.CAND022_CURRENT_SIGNAL_OBSERVATION))
        self.assertEqual(result["latest_position_source"], "current_signal_observation")
        self.assertIn("No KIS API call", result["note"])
        self.assertTrue(all(signal["action"] == "SET_TARGET_POSITION" for signal in result["signals"]))
        self.assertTrue(all("idempotency_key" in signal for signal in result["signals"]))

    def test_compute_signal_dispatches_cand022_without_submit_side_effects(self) -> None:
        result = loop_mod.compute_signal_for_candidate("CAND-022", "2026-05-14T09:00:00+09:00")

        self.assertTrue(result["ok"])
        self.assertEqual(loop_mod.SAFETY["broker_submit_allowed"], False)
        self.assertEqual(loop_mod.SAFETY["order_intent_created"], False)
        self.assertEqual(loop_mod.SAFETY["real_orders"], 0)

    def test_cand012_signal_computation_uses_local_daily_weights_only(self) -> None:
        result = loop_mod.compute_signal_for_candidate("CAND-012", "2026-05-14T09:00:00+09:00")

        self.assertTrue(result["ok"])
        self.assertEqual(result["portfolio_as_of"], "2026-05-07")
        self.assertGreater(result["symbol_count"], 0)
        self.assertIn("daily_weights", result["source_weights"])
        self.assertIn("No API call", result["note"])
        self.assertTrue(all(signal["action"] == "SET_TARGET_POSITION" for signal in result["signals"]))
        self.assertTrue(all(signal["target_weight"] > 0 for signal in result["signals"]))

    def test_cand022_readiness_reports_not_allowed_until_gate_pass_or_exception(self) -> None:
        readiness = loop_mod.check_shadow_readiness("CAND-022")

        self.assertFalse(readiness["ready"])
        self.assertIn(readiness["reason"], {"cand022_shadow_queue_not_allowed", "cand022_shadow_readiness_packet_missing"})

    def test_cand022_shadow_exception_acceptance_can_allow_no_submit_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            readiness_path = root / "stage6.json"
            acceptance_path = root / "acceptance.json"
            readiness_path.write_text(
                json.dumps(
                    {
                        "readiness_decision": "BLOCK",
                        "shadow_queue_allowed": False,
                        "blockers": ["kis_data_operation_ready_not_verified"],
                    }
                ),
                encoding="utf-8",
            )
            acceptance_path.write_text(
                json.dumps(
                    {
                        "candidate_id": "CAND-022",
                        "accepted_policy": "shadow_only_exception",
                        "scope": "NO_SUBMIT_REVIEW_ONLY",
                        "required_exact_instruction": loop_mod.CAND022_SHADOW_EXCEPTION_INSTRUCTION,
                        "is_approval": False,
                        "safety": loop_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )

            old_readiness = loop_mod.CAND022_SHADOW_READINESS
            old_acceptance = loop_mod.CAND022_SHADOW_EXCEPTION_ACCEPTANCE
            try:
                loop_mod.CAND022_SHADOW_READINESS = readiness_path
                loop_mod.CAND022_SHADOW_EXCEPTION_ACCEPTANCE = acceptance_path

                readiness = loop_mod.check_shadow_readiness("CAND-022")
            finally:
                loop_mod.CAND022_SHADOW_READINESS = old_readiness
                loop_mod.CAND022_SHADOW_EXCEPTION_ACCEPTANCE = old_acceptance

        self.assertTrue(readiness["ready"])
        self.assertEqual(readiness["reason"], "cand022_shadow_exception_accepted_no_submit")
        self.assertEqual(readiness["residual_blockers"], ["kis_data_operation_ready_not_verified"])
        self.assertIn("Paper, live, broker submit", readiness["note"])

    def test_cand022_invalid_shadow_exception_acceptance_stays_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            readiness_path = root / "stage6.json"
            acceptance_path = root / "acceptance.json"
            readiness_path.write_text(
                json.dumps(
                    {
                        "readiness_decision": "BLOCK",
                        "shadow_queue_allowed": False,
                        "blockers": ["human_mandate_incomplete"],
                    }
                ),
                encoding="utf-8",
            )
            acceptance_path.write_text(
                json.dumps(
                    {
                        "candidate_id": "CAND-022",
                        "accepted_policy": "shadow_only_exception",
                        "scope": "BROKER_PAPER",
                        "required_exact_instruction": loop_mod.CAND022_SHADOW_EXCEPTION_INSTRUCTION,
                        "is_approval": False,
                        "safety": loop_mod.SAFETY,
                    }
                ),
                encoding="utf-8",
            )

            old_readiness = loop_mod.CAND022_SHADOW_READINESS
            old_acceptance = loop_mod.CAND022_SHADOW_EXCEPTION_ACCEPTANCE
            try:
                loop_mod.CAND022_SHADOW_READINESS = readiness_path
                loop_mod.CAND022_SHADOW_EXCEPTION_ACCEPTANCE = acceptance_path

                readiness = loop_mod.check_shadow_readiness("CAND-022")
            finally:
                loop_mod.CAND022_SHADOW_READINESS = old_readiness
                loop_mod.CAND022_SHADOW_EXCEPTION_ACCEPTANCE = old_acceptance

        self.assertFalse(readiness["ready"])
        self.assertEqual(readiness["reason"], "cand022_shadow_queue_not_allowed")
        self.assertEqual(
            readiness["exception_acceptance"]["reason"],
            "cand022_shadow_exception_acceptance_invalid",
        )
        self.assertIn("scope", readiness["exception_acceptance"]["failed_checks"])

    def test_dry_run_report_is_per_candidate_and_no_write(self) -> None:
        report = loop_mod.build_dry_run_cycle_report(1, "2026-05-14T09:00:00+09:00")

        self.assertTrue(report["dry_run"])
        self.assertFalse(report["writes_files"])
        self.assertIn("candidate_reports", report)
        self.assertGreaterEqual(len(report["candidate_reports"]), 1)
        self.assertEqual(report["safety"], loop_mod.SAFETY)
        first = report["candidate_reports"][0]
        self.assertIn("candidate_id", first)
        self.assertIn("readiness_ok", first)
        self.assertIn("signal_ok", first)
        self.assertEqual(first["submit_mode"], "no_submit")

    def test_dry_run_can_inspect_cand022_before_queue_membership(self) -> None:
        report = loop_mod.build_dry_run_cycle_report(
            1,
            "2026-05-14T09:00:00+09:00",
            candidate_id="CAND-022",
        )

        self.assertTrue(report["dry_run"])
        self.assertFalse(report["writes_files"])
        self.assertEqual(report["shadow_queue_candidates"], ["CAND-022"])
        self.assertEqual(len(report["candidate_reports"]), 1)
        cand022 = report["candidate_reports"][0]
        self.assertEqual(cand022["candidate_id"], "CAND-022")
        self.assertEqual(cand022["queue_membership"], "dry_run_not_in_queue")
        self.assertEqual(cand022["symbol_count"], 7)
        self.assertEqual(cand022["latest_position_source"], "current_signal_observation")
        self.assertEqual(cand022["source_current_signal_observation"], str(loop_mod.CAND022_CURRENT_SIGNAL_OBSERVATION))
        self.assertEqual(cand022["submit_mode"], "no_submit")

    def test_cand022_shadow_record_carries_current_signal_source_for_audit(self) -> None:
        cycle_ts = "2026-05-14T09:00:00+09:00"
        signal = loop_mod.compute_signal_for_candidate("CAND-022", cycle_ts)
        readiness = {
            "ready": True,
            "reason": "cand022_shadow_exception_accepted_no_submit",
            "residual_blockers": ["kis_data_operation_ready_not_verified"],
        }
        ks_check = {"ok": True, "kill_switch_mode": "cancel_only"}

        record = loop_mod.build_shadow_signal_record(
            "CAND-022",
            "compressed_broe60_sroe80",
            cycle_ts,
            signal,
            readiness,
            ks_check,
        )

        self.assertEqual(
            record["source_files"]["cand022_current_signal_observation"],
            str(loop_mod.CAND022_CURRENT_SIGNAL_OBSERVATION),
        )
        self.assertEqual(record["source_files"]["cand022_mapping"], str(loop_mod.CAND022_MAPPING))
        self.assertEqual(record["submit_mode"], "no_submit")

    def test_cli_help_is_safe_for_cp949_console(self) -> None:
        result = subprocess.run(
            [sys.executable, str(MODULE_PATH), "--help"],
            cwd=str(MODULE_PATH.parent),
            env={"PYTHONIOENCODING": "cp949"},
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Stage 6 Shadow Loop - KIS no-submit signal recorder.", result.stdout)


if __name__ == "__main__":
    unittest.main()
