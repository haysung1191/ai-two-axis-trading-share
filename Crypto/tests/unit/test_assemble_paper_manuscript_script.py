from pathlib import Path

from scripts.assemble_paper_manuscript import build_manuscript


def test_build_manuscript_compiles_sections(tmp_path: Path) -> None:
    paper_dir = tmp_path / "paper"
    paper_dir.mkdir()

    files = {
        "title_candidates.md": "1. Test Title\n2. Backup Title\n",
        "abstract.md": "# Draft Abstract\n\nAbstract body.\n",
        "introduction.md": "# Intro\n\nIntro body.\n",
        "related_work.md": "# Related\n\nRelated body.\n",
        "method.md": "# Method\n\nMethod body.\n",
        "experiment_plan.md": "# Plan\n\nPlan body.\n",
        "results_section.md": "# Results\n\nResults body.\n",
        "discussion.md": "# Discussion\n\nDiscussion body.\n",
        "limitations.md": "# Limitations\n\nLimitations body.\n",
        "conclusion.md": "# Conclusion\n\nConclusion body.\n",
    }

    for name, text in files.items():
        (paper_dir / name).write_text(text, encoding="utf-8")

    manuscript = build_manuscript(paper_dir)

    assert "# Final Manuscript" in manuscript
    assert "## Working Title" in manuscript
    assert "Test Title" in manuscript
    assert "## Abstract" in manuscript
    assert "Abstract body." in manuscript
    assert "## Results" in manuscript
    assert "Results body." in manuscript
    assert "## Submission Readiness" in manuscript
