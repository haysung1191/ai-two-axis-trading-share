from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(r"C:\AI\run_gatekeeper_refresh_loop.py")
SPEC = importlib.util.spec_from_file_location("run_gatekeeper_refresh_loop", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
loop = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(loop)


class GatekeeperRefreshLoopTests(unittest.TestCase):
    def test_database_locked_failure_retries_then_succeeds(self) -> None:
        locked = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="sqlite3.OperationalError: database is locked")
        ok = subprocess.CompletedProcess(args=[], returncode=0, stdout="ok", stderr="")

        with tempfile.TemporaryDirectory() as tmp:
            original_log_dir = loop.LOG_DIR
            loop.LOG_DIR = Path(tmp)
            try:
                with (
                    patch.object(loop, "run_gatekeeper_once", side_effect=[locked, ok]),
                    patch.object(loop.time, "sleep", return_value=None) as sleep_mock,
                ):
                    result = loop.run_cycle("test_run", 1, lock_retries=3, lock_retry_sleep_seconds=0)
            finally:
                loop.LOG_DIR = original_log_dir

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["attempt_count"], 2)
        self.assertEqual(result["retryable_lock_retries_used"], 1)
        sleep_mock.assert_called_once()

    def test_non_lock_failure_does_not_retry(self) -> None:
        failed = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="ValueError: bad input")

        with tempfile.TemporaryDirectory() as tmp:
            original_log_dir = loop.LOG_DIR
            loop.LOG_DIR = Path(tmp)
            try:
                with (
                    patch.object(loop, "run_gatekeeper_once", return_value=failed) as run_mock,
                    patch.object(loop.time, "sleep", return_value=None) as sleep_mock,
                ):
                    result = loop.run_cycle("test_run", 1, lock_retries=3, lock_retry_sleep_seconds=0)
            finally:
                loop.LOG_DIR = original_log_dir

        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["attempt_count"], 1)
        self.assertEqual(run_mock.call_count, 1)
        sleep_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
