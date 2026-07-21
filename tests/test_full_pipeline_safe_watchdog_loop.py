from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import json


MODULE_PATH = Path(r"C:\AI\run_full_pipeline_safe_watchdog_loop.py")
SPEC = importlib.util.spec_from_file_location("run_full_pipeline_safe_watchdog_loop", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
watchdog = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = watchdog
SPEC.loader.exec_module(watchdog)


class FullPipelineSafeWatchdogLoopTests(unittest.TestCase):
    def test_zero_cycles_means_unbounded(self) -> None:
        self.assertTrue(watchdog.unbounded_cycles(0))
        self.assertEqual(watchdog.cycles_requested_value(0), "unbounded")

    def test_negative_cycles_also_mean_unbounded(self) -> None:
        self.assertTrue(watchdog.unbounded_cycles(-1))
        self.assertEqual(watchdog.cycles_requested_value(-1), "unbounded")

    def test_positive_cycles_are_finite(self) -> None:
        self.assertFalse(watchdog.unbounded_cycles(288))
        self.assertEqual(watchdog.cycles_requested_value(288), 288)

    def test_existing_watchdog_processes_excludes_current_pid(self) -> None:
        rows = [
            {"ProcessId": 111, "CommandLine": "python C:\\AI\\run_full_pipeline_safe_watchdog_loop.py --cycles 0"},
            {"ProcessId": 222, "CommandLine": "python C:\\AI\\run_full_pipeline_safe_watchdog_loop.py --cycles 0"},
        ]
        with patch("subprocess.run") as run, patch.object(watchdog.os, "getpid", return_value=111):
            run.return_value.returncode = 0
            run.return_value.stdout = json.dumps(rows)

            result = watchdog.existing_watchdog_processes()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["ProcessId"], 222)

    def test_existing_watchdog_processes_ignores_discovery_command(self) -> None:
        rows = [
            {
                "ProcessId": 333,
                "CommandLine": "powershell Get-CimInstance Win32_Process run_full_pipeline_safe_watchdog_loop.py",
            }
        ]
        with patch("subprocess.run") as run, patch.object(watchdog.os, "getpid", return_value=111):
            run.return_value.returncode = 0
            run.return_value.stdout = json.dumps(rows)

            result = watchdog.existing_watchdog_processes()

        self.assertEqual(result, [])

    def test_duplicate_exit_uses_separate_state_path(self) -> None:
        self.assertNotEqual(watchdog.DUPLICATE_EXIT_JSON, watchdog.LATEST_JSON)
        self.assertEqual(watchdog.DUPLICATE_EXIT_JSON.name, "full_pipeline_safe_watchdog_duplicate_exit_latest.json")


if __name__ == "__main__":
    unittest.main()
