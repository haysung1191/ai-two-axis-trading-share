from __future__ import annotations

import importlib.util
import unittest
from datetime import date
from pathlib import Path


SIGNAL_MODULE_PATH = Path(r"C:\AI\build_cand022_current_signal_observation.py")
SIGNAL_SPEC = importlib.util.spec_from_file_location("build_cand022_current_signal_observation", SIGNAL_MODULE_PATH)
assert SIGNAL_SPEC is not None
assert SIGNAL_SPEC.loader is not None
signal_mod = importlib.util.module_from_spec(SIGNAL_SPEC)
SIGNAL_SPEC.loader.exec_module(signal_mod)

STAGE6_MODULE_PATH = Path(r"C:\AI\build_cand022_stage6_shadow_readiness_packet.py")
STAGE6_SPEC = importlib.util.spec_from_file_location("build_cand022_stage6_shadow_readiness_packet", STAGE6_MODULE_PATH)
assert STAGE6_SPEC is not None
assert STAGE6_SPEC.loader is not None
stage6_mod = importlib.util.module_from_spec(STAGE6_SPEC)
STAGE6_SPEC.loader.exec_module(stage6_mod)


class Cand022CurrentSignalObservationTests(unittest.TestCase):
    def test_valid_current_signal_observation_requires_signal_only_safety_and_fresh_observation(self) -> None:
        observation = {
            "candidate_id": "CAND-022",
            "scope": "signal_only_no_submit",
            "status": "PASS",
            "safety": signal_mod.SAFETY,
            "position_count": 5,
            "observation_date": "2026-05-14",
        }

        ok, age_days, failed = stage6_mod.valid_current_signal_observation(observation, date(2026, 5, 14))

        self.assertTrue(ok)
        self.assertEqual(age_days, 0)
        self.assertEqual(failed, [])

    def test_valid_current_signal_observation_rejects_submit_scope(self) -> None:
        observation = {
            "candidate_id": "CAND-022",
            "scope": "broker_submit",
            "status": "PASS",
            "safety": signal_mod.SAFETY,
            "position_count": 5,
            "observation_date": "2026-05-14",
        }

        ok, _, failed = stage6_mod.valid_current_signal_observation(observation, date(2026, 5, 14))

        self.assertFalse(ok)
        self.assertIn("current_signal_observation_scope_not_signal_only", failed)


if __name__ == "__main__":
    unittest.main()
