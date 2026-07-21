from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.domains.experiments.btc_1d_pullthrough_asymmetric_release_reframe_batch import (
    Btc1dPullthroughAsymmetricReleaseReframeBatchService,
    Btc1dPullthroughAsymmetricReleaseReframeConfig,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the BTC 1d pullthrough asymmetric release reframe batch.")
    parser.add_argument("--analysis-dir", type=Path, default=Path("analysis_results"))
    parser.add_argument("--periods", type=int, default=2200)
    parser.add_argument("--allow-synthetic-ohlcv-fallback", action="store_true")
    args = parser.parse_args()

    service = Btc1dPullthroughAsymmetricReleaseReframeBatchService(analysis_results_dir=args.analysis_dir)
    result = service.run_batch(
        Btc1dPullthroughAsymmetricReleaseReframeConfig(
            periods=args.periods,
            allow_synthetic_ohlcv_fallback=args.allow_synthetic_ohlcv_fallback,
        )
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
