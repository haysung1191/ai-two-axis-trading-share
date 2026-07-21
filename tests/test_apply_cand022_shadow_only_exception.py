from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\apply_cand022_shadow_only_exception.py")
SPEC = importlib.util.spec_from_file_location("apply_cand022_shadow_only_exception", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
apply_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(apply_mod)


class ApplyCand022ShadowOnlyExceptionTests(unittest.TestCase):
    def _write_inputs(self, root: Path) -> dict[str, Path]:
        paths = {
            "contract_path": root / "contract.json",
            "stage6_readiness_path": root / "stage6.json",
            "closure_plan_path": root / "closure.json",
            "queue_path": root / "shadow_queue.jsonl",
            "acceptance_latest": root / "acceptance.latest.json",
        }
        paths["contract_path"].write_text(
            json.dumps(
                {
                    "status": "READY_REVIEW_ONLY_SHADOW_EXCEPTION_CONTRACT",
                    "is_approval": False,
                    "auto_apply_allowed": False,
                    "required_explicit_operator_instruction_before_any_contract_change": apply_mod.REQUIRED_INSTRUCTION,
                    "safety": apply_mod.SAFETY,
                }
            ),
            encoding="utf-8",
        )
        paths["stage6_readiness_path"].write_text(
            json.dumps(
                {
                    "shadow_queue_allowed": False,
                    "shadow_passed": False,
                    "stage5_evidence": {"stage5_evidence_passed": True},
                }
            ),
            encoding="utf-8",
        )
        paths["closure_plan_path"].write_text(
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
        paths["queue_path"].write_text(json.dumps({"candidate_id": "CAND-001"}) + "\n", encoding="utf-8")
        return paths

    def test_blocks_without_exact_instruction_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = self._write_inputs(Path(tmp))
            report = apply_mod.apply_exception(
                "wrong instruction",
                dry_run=False,
                generated_at="2026-05-14T09:30:00+09:00",
                report_path=Path(tmp) / "apply_report.json",
                **paths,
            )
            queue_text = paths["queue_path"].read_text(encoding="utf-8")

        self.assertEqual(report["status"], "BLOCK_SHADOW_ONLY_EXCEPTION_APPLY")
        self.assertIn("operator_instruction_exact_match", report["blockers"])
        self.assertFalse(report["wrote_acceptance"])
        self.assertFalse(paths["acceptance_latest"].exists())
        self.assertNotIn("CAND-022", queue_text)

    def test_dry_run_ready_with_exact_instruction_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = self._write_inputs(Path(tmp))
            report = apply_mod.apply_exception(
                apply_mod.REQUIRED_INSTRUCTION,
                dry_run=True,
                generated_at="2026-05-14T09:30:00+09:00",
                report_path=Path(tmp) / "apply_report.json",
                **paths,
            )
            queue_text = paths["queue_path"].read_text(encoding="utf-8")

        self.assertEqual(report["status"], "DRY_RUN_READY_TO_APPLY_SHADOW_ONLY_EXCEPTION")
        self.assertFalse(report["wrote_acceptance"])
        self.assertFalse(report["appended_shadow_queue"])
        self.assertFalse(paths["acceptance_latest"].exists())
        self.assertNotIn("CAND-022", queue_text)
        self.assertEqual(report["safety"], apply_mod.SAFETY)
        self.assertIn("run_stage6_shadow_loop.py --cycles 1 --dry-run", " ".join(report["dry_run_preview_verification_commands"]))
        self.assertEqual(report["post_apply_verification_commands"], [])

    def test_applies_acceptance_and_appends_no_submit_shadow_queue_with_exact_instruction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = self._write_inputs(Path(tmp))
            report = apply_mod.apply_exception(
                apply_mod.REQUIRED_INSTRUCTION,
                dry_run=False,
                generated_at="2026-05-14T09:30:00+09:00",
                report_path=Path(tmp) / "apply_report.json",
                **paths,
            )
            acceptance = json.loads(paths["acceptance_latest"].read_text(encoding="utf-8"))
            queue_rows = [
                json.loads(line)
                for line in paths["queue_path"].read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

        self.assertEqual(report["status"], "APPLIED_SHADOW_ONLY_EXCEPTION")
        self.assertTrue(report["wrote_acceptance"])
        self.assertTrue(report["appended_shadow_queue"])
        self.assertEqual(acceptance["candidate_id"], "CAND-022")
        self.assertEqual(acceptance["accepted_policy"], "shadow_only_exception")
        self.assertEqual(acceptance["scope"], "NO_SUBMIT_REVIEW_ONLY")
        self.assertFalse(acceptance["is_approval"])
        self.assertEqual(acceptance["safety"], apply_mod.SAFETY)
        self.assertEqual(queue_rows[-1]["candidate_id"], "CAND-022")
        self.assertEqual(queue_rows[-1]["decision"], "PASS_TO_NEXT_QUEUE")
        self.assertEqual(queue_rows[-1]["safety_snapshot"], apply_mod.SAFETY)
        self.assertIn("build_cand022_stage6_shadow_readiness_packet.py", " ".join(report["post_apply_verification_commands"]))
        self.assertIn("run_cand022_provider_response_refresh_stack.py", " ".join(report["post_apply_verification_commands"]))
        self.assertEqual(report["dry_run_preview_verification_commands"], [])

    def test_existing_acceptance_is_successful_idempotent_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = self._write_inputs(Path(tmp))
            acceptance = apply_mod.build_acceptance("2026-05-14T09:30:00+09:00", apply_mod.REQUIRED_INSTRUCTION)
            paths["acceptance_latest"].write_text(json.dumps(acceptance), encoding="utf-8")
            queue_row = apply_mod.build_queue_row("2026-05-14T09:30:00+09:00", paths["acceptance_latest"])
            with paths["queue_path"].open("a", encoding="utf-8") as f:
                f.write(json.dumps(queue_row) + "\n")

            report = apply_mod.apply_exception(
                apply_mod.REQUIRED_INSTRUCTION,
                dry_run=True,
                generated_at="2026-05-14T09:31:00+09:00",
                report_path=Path(tmp) / "apply_report.json",
                **paths,
            )

        self.assertEqual(report["status"], "SHADOW_ONLY_EXCEPTION_ALREADY_ACTIVE")
        self.assertTrue(report["already_active"])
        self.assertEqual(report["blockers"], [])
        self.assertFalse(report["wrote_acceptance"])
        self.assertFalse(report["appended_shadow_queue"])


if __name__ == "__main__":
    unittest.main()
