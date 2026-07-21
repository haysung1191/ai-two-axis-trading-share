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


STAGE2_VARIANT_LABELS: tuple[str, ...] = (
    "trend9504_depth055_volume104_stop22_hold36",
    "trend9504_depth055_volume104_hold32",
    "trend9504_depth055_volume104_stop22_hold32",
    "trend1056_depth055_volume104_stop22_hold36",
    "trend1056_depth055_volume100_stop22_hold32",
    "trend1056_depth055_volume104_stop22_hold32",
)


def main() -> int:
    service = Btc1dPostSpikeConsolidationBreakoutWalkForwardRepairBatchService(
        analysis_results_dir=Path("analysis_results")
    )
    result = service.run_batch(
        Btc1dPostSpikeConsolidationBreakoutWalkForwardRepairConfig(
            variant_labels=STAGE2_VARIANT_LABELS,
            artifact_stem="btc_1d_post_spike_idle_window_followup_stage2_batch",
        )
    )
    print(
        json.dumps(
            {
                "artifact_stem": "btc_1d_post_spike_idle_window_followup_stage2_batch",
                "variant_labels": list(STAGE2_VARIANT_LABELS),
                "result": result,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
