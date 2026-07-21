from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_cand022_shadow_exception_apply_preflight.py")
SPEC = importlib.util.spec_from_file_location("build_cand022_shadow_exception_apply_preflight", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
preflight_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preflight_mod)


class Cand022ShadowExceptionApplyPreflightTests(unittest.TestCase):
    def _write_inputs(self, root: Path) -> dict[str, Path]:
        paths = {
            "contract": root / "contract.json",
            "stage6": root / "stage6.json",
            "closure": root / "closure.json",
            "queue": root / "shadow_queue.jsonl",
        }
        paths["contract"].write_text(
            json.dumps(
                {
                    "status": "READY_REVIEW_ONLY_SHADOW_EXCEPTION_CONTRACT",
                    "is_approval": False,
                    "auto_apply_allowed": False,
                    "required_explicit_operator_instruction_before_any_contract_change": (
                        "APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY"
                    ),
                    "safety": preflight_mod.SAFETY,
                }
            ),
            encoding="utf-8",
        )
        paths["stage6"].write_text(
            json.dumps(
                {
                    "shadow_queue_allowed": False,
                    "shadow_passed": False,
                    "stage5_evidence": {"stage5_evidence_passed": True},
                }
            ),
            encoding="utf-8",
        )
        paths["closure"].write_text(
            json.dumps(
                {
                    "stage6_recorder_support": {
                        "cand022_signal_computation_present": True,
                        "cand022_dispatch_present": True,
                        "per_candidate_dry_run_present": True,
                        "no_submit_safety_present": True,
                    }
                }
            ),
            encoding="utf-8",
        )
        paths["queue"].write_text(json.dumps({"candidate_id": "CAND-001"}) + "\n", encoding="utf-8")
        return paths

    def test_preflight_waits_without_exact_instruction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = self._write_inputs(Path(tmp))
            report = preflight_mod.build_preflight(
                "2026-05-14T09:00:00+09:00",
                contract_path=paths["contract"],
                stage6_readiness_path=paths["stage6"],
                closure_plan_path=paths["closure"],
                queue_path=paths["queue"],
            )

        self.assertEqual(report["status"], "WAIT_EXPLICIT_SHADOW_ONLY_EXCEPTION_INSTRUCTION")
        self.assertFalse(report["can_apply_now"])
        self.assertEqual(report["blocked_checks"], ["operator_instruction_exact_match"])
        self.assertIn("do_not_apply_without_exact_instruction", report["forbidden_actions"])
        self.assertIn("run_cand022_shadow_only_exception_apply_and_verify.py", report["guarded_apply_commands"]["dry_run"])
        self.assertNotIn("--execute", report["guarded_apply_commands"]["dry_run"])
        self.assertIn("--execute", report["guarded_apply_commands"]["apply"])
        self.assertIn("--i-confirm-apply-shadow-only-exception", report["guarded_apply_commands"]["apply"])
        self.assertEqual(
            report["confirm_flag_required_for_real_apply"],
            "--i-confirm-apply-shadow-only-exception",
        )
        self.assertTrue(report["real_apply_requires_execute_flag"])
        self.assertTrue(report["low_level_apply_script_is_not_operator_surface"])
        self.assertIn("APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY", report["guarded_apply_commands"]["apply"])
        self.assertIn(
            "python .\\build_cand022_stage6_shadow_readiness_packet.py",
            report["post_apply_verification_commands"],
        )
        self.assertIn(
            "python .\\run_stage6_shadow_loop.py --cycles 1 --dry-run",
            report["post_apply_verification_commands"],
        )
        self.assertFalse(report["safety"]["broker_submit_allowed"])

    def test_preflight_ready_with_exact_instruction_but_still_does_not_apply(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = self._write_inputs(Path(tmp))
            report = preflight_mod.build_preflight(
                "2026-05-14T09:00:00+09:00",
                operator_instruction="APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY",
                contract_path=paths["contract"],
                stage6_readiness_path=paths["stage6"],
                closure_plan_path=paths["closure"],
                queue_path=paths["queue"],
            )
            queue_text = paths["queue"].read_text(encoding="utf-8")

        self.assertEqual(report["status"], "READY_TO_APPLY_SHADOW_ONLY_EXCEPTION_IF_GUARDED_WRITER_IS_RUN")
        self.assertTrue(report["can_apply_now"])
        self.assertEqual(report["blocked_checks"], [])
        self.assertIn('"CAND-001"', queue_text)
        self.assertNotIn("CAND-022", queue_text)
        self.assertIn("acceptance_latest_json", report["would_write_if_guarded_apply_runs_later"])
        self.assertIn("run_cand022_shadow_only_exception_apply_and_verify.py", report["guarded_apply_commands"]["apply"])
        self.assertIn("--execute", report["guarded_apply_commands"]["apply"])
        self.assertIn("--i-confirm-apply-shadow-only-exception", report["guarded_apply_commands"]["apply"])
        self.assertIn("run_cand022_provider_response_refresh_stack.py", " ".join(report["post_apply_verification_commands"]))

    def test_preflight_blocks_if_queue_already_has_cand022(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = self._write_inputs(Path(tmp))
            paths["queue"].write_text(json.dumps({"candidate_id": "CAND-022"}) + "\n", encoding="utf-8")
            report = preflight_mod.build_preflight(
                "2026-05-14T09:00:00+09:00",
                operator_instruction="APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY",
                contract_path=paths["contract"],
                stage6_readiness_path=paths["stage6"],
                closure_plan_path=paths["closure"],
                queue_path=paths["queue"],
            )

        self.assertEqual(report["status"], "BLOCK_SHADOW_ONLY_EXCEPTION_PREFLIGHT")
        self.assertIn("queue_does_not_already_contain_cand022", report["blocked_checks"])


if __name__ == "__main__":
    unittest.main()
