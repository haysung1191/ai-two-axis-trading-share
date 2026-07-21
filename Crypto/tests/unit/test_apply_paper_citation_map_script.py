from pathlib import Path

from scripts.apply_paper_citation_map import apply_mapping, apply_mapping_to_dir


def test_apply_mapping_replaces_known_tokens() -> None:
    text = "See [LLM-FIN-1; VALID-2], but keep AUTO-STRAT-9 if unmapped."
    mapping = {
        "LLM-FIN-1": "smith2024llmfinance",
        "VALID-2": "bailey2014overfitting",
    }

    updated = apply_mapping(text, mapping)

    assert "smith2024llmfinance" in updated
    assert "bailey2014overfitting" in updated
    assert "AUTO-STRAT-9" in updated


def test_apply_mapping_to_dir_updates_markdown_files(tmp_path: Path) -> None:
    paper_dir = tmp_path / "paper"
    paper_dir.mkdir()
    target = paper_dir / "related_work.md"
    target.write_text("Ref LLM-FIN-1 and VALID-1.\n", encoding="utf-8")
    (paper_dir / "notes.txt").write_text("LLM-FIN-1\n", encoding="utf-8")

    updated = apply_mapping_to_dir(
        paper_dir,
        {
            "LLM-FIN-1": "cite_a",
            "VALID-1": "cite_b",
        },
    )

    assert updated == [target]
    assert target.read_text(encoding="utf-8") == "Ref cite_a and cite_b.\n"
