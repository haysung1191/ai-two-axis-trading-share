from pathlib import Path

from scripts.validate_paper_placeholders import scan_placeholders


def test_scan_placeholders_reports_matches(tmp_path: Path) -> None:
    paper_dir = tmp_path / "paper"
    paper_dir.mkdir()
    (paper_dir / "related_work.md").write_text(
        "Ref [LLM-FIN-1; VALID-2]\nAnother [TAI-3]\n",
        encoding="utf-8",
    )
    (paper_dir / "abstract.md").write_text("No placeholders here\n", encoding="utf-8")

    report = scan_placeholders(paper_dir)

    assert report["total_placeholders"] == 3
    assert report["counts"]["LLM-FIN-1"] == 1
    assert report["counts"]["VALID-2"] == 1
    assert report["counts"]["TAI-3"] == 1
    assert "related_work.md" in report["files"]
