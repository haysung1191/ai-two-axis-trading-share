# Root Script Reorg Manifest

## Why

The repository root has grown into a mixed landing zone for research scripts, operator tools, data ingestion jobs, dashboards, and entrypoints. This manifest defines the first safe reorganization boundary before any physical file moves happen.

The goal is to reduce root-level clutter without breaking imports or CLI entrypoints. We are explicitly separating:

- research analysis scripts
- data ingestion / backfill scripts
- operator and archive tooling
- pipeline runners
- dashboards
- root/core modules that should stay put until a later dependency pass

## Current Inventory

Machine-readable inventory:

- [root_script_inventory.csv](/C:/AI/momentum/output/repo_script_manifest/root_script_inventory.csv)
- [root_script_inventory_summary.json](/C:/AI/momentum/output/repo_script_manifest/root_script_inventory_summary.json)

Current root Python file count: `34`

Category counts:

- `research`: `6`
- `operations`: `6`
- `data_ingestion`: `0`
- `core`: `20`
- `pipelines`: `2`
- `dashboards`: `0`
- `uncategorized`: `0`

Completed so far:

- all `analyze_split_models_*.py` scripts were moved out of root into `tools/analysis`
- all split-model `build_*`, `check_*`, and `archive_*` operator scripts were moved out of root into `tools/operations`
- all split-model `run_*` pipeline scripts were moved out of root into `tools/pipelines`
- all `*_backfill.py`, `build_*cache.py`, and `refresh_*` ingestion scripts were moved out of root into `tools/data_ingestion`
- all current `kis_*_eval.py`, `kis_*_compare.py`, `kis_*_report.py`, `us_*`, `backtest_*`, and `event_*` research scripts were moved out of root into `tools/research`
- `plot_us_momentum_paper_figures.py` was moved out of root into `tools/plotting`
- `split_models_shadow_dashboard.py` was moved out of root into `tools/dashboards`
- `shadow_dashboard.py` was moved out of root into `tools/dashboards`
- `dashboard.py` was moved out of root into `tools/dashboards` after decoupling the Docker web entrypoint

## Proposed Target Layout

- `tools/analysis`
  - `analyze_*` scripts and split-model robustness/benchmark studies
- `tools/research`
  - research-only backtests, evals, compare/report utilities, US-specific strategy experiments
- `tools/data_ingestion`
  - `*_backfill.py`, cache builders, metadata refresh, data coverage refresh
- `tools/operations`
  - `build_*`, `check_*`, `archive_*`, operator packet/readiness/drift helpers, monthly packet publishing
- `tools/pipelines`
  - `run_*` scripts that orchestrate multi-step flows
- `tools/plotting`
  - figure-generation scripts
- `tools/dashboards`
  - dashboard launchers that are not app entrypoints

## Hold In Place For Now

These should not move in the first wave because they are likely imported broadly or act as user-facing entrypoints:

- `config.py`
- `main.py`
- `kis_api.py`
- `screener.py`
- `kis_backtest_from_prices.py`
- `kis_flow_data.py`
- `kis_flow_signal.py`
- `kis_quality_data.py`
- `kis_shadow_common.py`
- `kis_shadow_*` shared modules

## First Safe Move Wave

The safest first relocation wave is scripts that are root-level CLIs and have low import risk:

1. data-ingestion and research script waves

Why this wave first:

- these files already behave like standalone utilities
- they mostly consume repo modules rather than being imported as shared libraries
- they align directly with the new folder taxonomy

## Second Move Wave

After split-model, data-ingestion, and research tools stabilized:

1. `plot_us_momentum_paper_figures.py` -> `tools/plotting` (completed)

## Manual Review Bucket

The original manual-review bucket is now closed for the currently inventoried root files.

Resolved handling:

- keep `config.py` in root as a core runtime settings module because many root and tools modules still import `config` directly
- keep `main.py` in root as a core runtime entrypoint because `Dockerfile` and `Dockerfile.job` still execute `python main.py`
- keep `screener.py` in root only as a backward-compatible import shim; the implementation now lives in `live_core/kis_screener.py`

## Move Rules

Before any real move:

1. Move one category at a time.
2. Update imports and CLI references in the same commit.
3. Add or update smoke tests for moved entrypoints.
4. Keep backwards-compatible stubs only if an external script or automation depends on the old path.
5. Prefer manifest-driven moves over ad hoc renames.

## Next Step

The next highest-value move is a root/core decoupling pass rather than more category moves:

- decouple `main.py` and `screener.py` from Docker/runtime entrypoints if a later `app/` or `tools/` migration is desired
- decouple broad `import config` usage if a later settings-module relocation is desired
