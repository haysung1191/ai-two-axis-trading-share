# Paper Build Instructions

Use the package builder when the artifact archive or any paper fragment changes.

## One-command rebuild

```bash
python scripts/build_paper_package.py
```

This regenerates:

1. `paper_results/`
2. `paper_figures/`
3. `docs/paper/final_manuscript_compiled.md`
4. `docs/paper/placeholder_report.json` after running the placeholder validator separately

## Individual rebuild steps

```bash
python scripts/export_paper_results.py --artifacts-root artifacts --output-dir paper_results --registry-path strategy_registry.json
python scripts/build_paper_figures.py --paper-results-dir paper_results --output-dir paper_figures
python scripts/assemble_paper_manuscript.py --paper-dir docs/paper --output docs/paper/final_manuscript_compiled.md
```

## When to rebuild

- after running new benchmark experiments
- after changing any paper section in `docs/paper/`
- after changing result-export logic
- after changing figure-generation logic

## Review order

1. `docs/paper/final_manuscript_compiled.md`
2. `docs/paper/results_tables.md`
3. `docs/paper/figure_captions.md`
4. `paper_figures/figure_manifest.json`
5. `docs/paper/placeholder_report.json`

## Placeholder audit

```bash
python scripts/validate_paper_placeholders.py --paper-dir docs/paper --output docs/paper/placeholder_report.json
```

## Citation mapping apply step

After external literature results are mapped into `docs/paper/citation_mapping_template.json` and `docs/paper/references_template.bib`, run:

```bash
python scripts/apply_paper_citation_map.py --paper-dir docs/paper --mapping docs/paper/citation_mapping_template.json
python scripts/validate_paper_placeholders.py --paper-dir docs/paper --output docs/paper/placeholder_report.json
python scripts/build_paper_package.py
```

## Clean benchmark batch

Smoke run:

```bash
python scripts/run_clean_benchmark.py --groups full_system no_mutation --repetitions 1 --max-iterations 3 --talk-delay-sec 0 --manifest paper_results/clean_benchmark_manifest_smoke.json
python scripts/summarize_clean_benchmark.py --artifacts-root artifacts --output paper_results/clean_benchmark_summary.csv
```

Full batch:

```bash
python scripts/run_clean_benchmark.py --repetitions 30 --max-iterations 6 --talk-delay-sec 0 --manifest paper_results/clean_benchmark_manifest.json
python scripts/summarize_clean_benchmark.py --artifacts-root artifacts --output paper_results/clean_benchmark_summary.csv
python scripts/build_paper_package.py
```
