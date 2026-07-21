from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.domains.experiments.btc_1d_post_spike_consolidation_breakout_walk_forward_repair_batch import (
    Btc1dPostSpikeConsolidationBreakoutWalkForwardRepairBatchService,
    Btc1dPostSpikeConsolidationBreakoutWalkForwardRepairConfig,
)


IDLE_AXIS_VARIANT_LABELS: tuple[str, ...] = (
    "trend1056_depth055_volume104_stop22_hold36",
    "trend1056_depth055_volume104_stop22_hold36_buffer0015",
    "trend1056_depth055_volume104_stop22_hold36_buffer0025",
    "trend1056_depth055_volume104_stop22_hold36_consol6",
    "trend1056_depth055_volume104_stop22_hold36_consol8",
    "trend1056_depth055_volume104_stop22_hold36_spike20",
    "trend1056_depth055_volume104_stop22_hold36_spike28",
    "trend1056_depth055_volume104_stop22_hold36_minspike080",
    "trend1056_depth055_volume104_stop22_hold36_minspike090",
)


def main() -> int:
    service = Btc1dPostSpikeConsolidationBreakoutWalkForwardRepairBatchService(
        analysis_results_dir=Path("analysis_results")
    )
    result = service.run_batch(
        Btc1dPostSpikeConsolidationBreakoutWalkForwardRepairConfig(
            variant_labels=IDLE_AXIS_VARIANT_LABELS,
            artifact_stem="btc_1d_post_spike_idle_window_axis_batch",
        )
    )
    print(
        json.dumps(
            {
                "artifact_stem": "btc_1d_post_spike_idle_window_axis_batch",
                "variant_labels": list(IDLE_AXIS_VARIANT_LABELS),
                "result": result,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
