from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PAPER_DIR = ROOT / "docs" / "paper"
DEFAULT_MAP_PATH = DEFAULT_PAPER_DIR / "citation_mapping_template.json"


PLACEHOLDER_TOKEN = re.compile(r"\b(?:LLM-FIN|AUTO-STRAT|VALID|TAI)-\d+\b")


def apply_mapping(text: str, mapping: dict[str, str]) -> str:
    def _replace(match: re.Match[str]) -> str:
        token = match.group(0)
        return mapping.get(token, token)

    return PLACEHOLDER_TOKEN.sub(_replace, text)


def apply_mapping_to_dir(paper_dir: Path, mapping: dict[str, str]) -> list[Path]:
    updated: list[Path] = []
    for path in sorted(paper_dir.glob("*.md")):
        original = path.read_text(encoding="utf-8")
        replaced = apply_mapping(original, mapping)
        if replaced != original:
            path.write_text(replaced, encoding="utf-8")
            updated.append(path)
    return updated


def load_mapping(mapping_path: Path) -> dict[str, str]:
    payload = json.loads(mapping_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Citation mapping must be a JSON object.")
    return {str(key): str(value) for key, value in payload.items()}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Apply citation placeholder mappings to docs/paper markdown files."
    )
    parser.add_argument(
        "--paper-dir",
        type=Path,
        default=DEFAULT_PAPER_DIR,
        help="Directory containing paper markdown files.",
    )
    parser.add_argument(
        "--mapping",
        type=Path,
        default=DEFAULT_MAP_PATH,
        help="JSON file mapping placeholders to citation keys or inline citations.",
    )
    args = parser.parse_args()

    mapping = load_mapping(args.mapping)
    updated = apply_mapping_to_dir(args.paper_dir, mapping)
    print(f"Updated {len(updated)} file(s).")
    for path in updated:
        print(path)


if __name__ == "__main__":
    main()
