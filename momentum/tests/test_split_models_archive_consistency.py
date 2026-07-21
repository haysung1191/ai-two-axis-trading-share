from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from tools.operations import check_split_models_archive_consistency as archive_consistency


def test_split_models_archive_consistency_passes_for_aligned_files(tmp_path: Path, monkeypatch, capsys) -> None:
    shadow_dir = tmp_path / "shadow"
    archive_dir = tmp_path / "archive"
    latest_dir = archive_dir / "20260414T120500"
    prior_dir = archive_dir / "20260414T120000"
    shadow_dir.mkdir(parents=True)
    latest_dir.mkdir(parents=True)
    prior_dir.mkdir(parents=True)

    latest_runtime_status = {
        "baseline_variant": "rule_breadth_it_us5_cap",
        "archive_latest_run_id": "20260414T120500",
        "archive_prior_run_id": "20260414T120000",
        "live_readiness": "GO",
    }
    prior_runtime_status = {
        "baseline_variant": "rule_breadth_it_us5_cap",
        "archive_latest_run_id": "20260414T120000",
        "archive_prior_run_id": None,
        "live_readiness": "GO",
    }
    delta = {
        "latest_run_id": "20260414T120500",
        "prior_run_id": "20260414T120000",
        "latest_runtime_status": latest_runtime_status,
        "prior_runtime_status": prior_runtime_status,
    }
    manifest = pd.DataFrame(
        [
            {
                "RunId": "20260414T120000",
                "CurrentHoldings": 8,
                "CurrentDominantSector": "Industrials",
                "ArchivePath": str(prior_dir),
            },
            {
                "RunId": "20260414T120500",
                "CurrentHoldings": 8,
                "CurrentDominantSector": "Industrials",
                "ArchivePath": str(latest_dir),
            },
        ]
    )
    latest_summary = {
        "baseline_variant": "rule_breadth_it_us5_cap",
        "current_holdings": 8,
        "current_dominant_sector": "Industrials",
    }

    (shadow_dir / "shadow_operator_runtime_status.json").write_text(
        json.dumps(latest_runtime_status, indent=2), encoding="utf-8"
    )
    (latest_dir / "shadow_operator_runtime_status.json").write_text(
        json.dumps(latest_runtime_status, indent=2), encoding="utf-8"
    )
    (prior_dir / "shadow_operator_runtime_status.json").write_text(
        json.dumps(prior_runtime_status, indent=2), encoding="utf-8"
    )
    (latest_dir / "shadow_summary.json").write_text(json.dumps(latest_summary, indent=2), encoding="utf-8")
    (archive_dir / "archive_latest_delta.json").write_text(json.dumps(delta, indent=2), encoding="utf-8")
    manifest.to_csv(archive_dir / "archive_manifest.csv", index=False, encoding="utf-8-sig")

    monkeypatch.setattr(archive_consistency, "SHADOW_DIR", shadow_dir)
    monkeypatch.setattr(archive_consistency, "ARCHIVE_DIR", archive_dir)
    monkeypatch.setattr(archive_consistency, "REPORT_PATH", archive_dir / "archive_consistency_report.json")

    archive_consistency.main()

    report = json.loads((archive_dir / "archive_consistency_report.json").read_text(encoding="utf-8"))
    assert report["archive_consistency_verdict"] == "PASS"
    assert all(check["Passed"] for check in report["checks"])
    output = capsys.readouterr().out
    assert "archive_consistency_verdict=PASS" in output
