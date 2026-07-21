from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.domains.experiments.btc_1d_post_spike_trend_gate_relaxation_batch import (
    Btc1dPostSpikeTrendGateRelaxationBatchService,
    Btc1dPostSpikeTrendGateRelaxationConfig,
)


def main() -> int:
    service = Btc1dPostSpikeTrendGateRelaxationBatchService(
        analysis_results_dir=Path("analysis_results")
    )
    result = service.run_batch(Btc1dPostSpikeTrendGateRelaxationConfig())
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
