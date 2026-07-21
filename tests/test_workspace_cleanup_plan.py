from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(r"C:\AI\build_workspace_cleanup_plan.py")
SPEC = importlib.util.spec_from_file_location("build_workspace_cleanup_plan", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
cleanup_plan = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cleanup_plan)


class WorkspaceCleanupPlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.old_root = cleanup_plan.ROOT
        root = Path(self.tmp.name)
        (root / "overnight_runs").mkdir()
        (root / "ops/runstate").mkdir(parents=True)
        (root / "reports/operations").mkdir(parents=True)
        (root / "research_lane_stage1/latest").mkdir(parents=True)
        (root / "research_lane_stage2/latest").mkdir(parents=True)
        (root / "research_lane_stage3/latest").mkdir(parents=True)
        (root / "Crypto/analysis_results").mkdir(parents=True)
        (root / "sample.py").write_text("print('x')\n", encoding="utf-8")
        (root / "Crypto/analysis_results/result.json").write_text("{}", encoding="utf-8")
        (root / "overnight_runs/DISABLE_DUAL_REPO_RESEARCH_LOOP").write_text("", encoding="utf-8")
        (root / "ops/runstate/kill_switch.json").write_text("{}", encoding="utf-8")
        (root / "reports/operations/pipeline_direct_recheck_latest.json").write_text("{}", encoding="utf-8")
        cleanup_plan.ROOT = root

    def tearDown(self) -> None:
        cleanup_plan.ROOT = self.old_root

    def test_plan_preserves_hard_safety_paths(self) -> None:
        plan = cleanup_plan.build_plan()
        protected = set(plan["safety_policy"]["do_not_delete_paths"])

        self.assertIn("overnight_runs/DISABLE_DUAL_REPO_RESEARCH_LOOP", protected)
        self.assertIn("ops/runstate/kill_switch.json", protected)
        self.assertIn("reports/operations/pipeline_direct_recheck_latest.json", protected)
        self.assertEqual(plan["safety_policy"]["delete_now"], "none")
        self.assertEqual(plan["safety_policy"]["move_now"], "none")

    def test_plan_reports_current_totals_and_cleanup_targets(self) -> None:
        plan = cleanup_plan.build_plan()
        cleaned = {row["path"]: row["exists"] for row in plan["recently_cleaned_path_status"]}

        self.assertGreater(plan["current_totals"]["file_count"], 0)
        self.assertGreater(plan["current_totals"]["bytes"], 0)
        self.assertIn("reports/operations/runs", cleaned)
        self.assertIn("__pycache__", cleaned)
        self.assertIn(".pytest_cache", cleaned)

    def test_archive_candidates_are_policy_gated(self) -> None:
        plan = cleanup_plan.build_plan()
        candidates = {row["path"]: row for row in plan["archive_candidates"]}

        crypto = candidates["Crypto/analysis_results"]
        self.assertEqual(crypto["recommended_action"], "archive_policy_required_no_direct_delete")
        self.assertIn("retention_requirement", crypto)


if __name__ == "__main__":
    unittest.main()
