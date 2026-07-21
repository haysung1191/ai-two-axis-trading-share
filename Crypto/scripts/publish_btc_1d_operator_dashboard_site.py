from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_btc_1d_operator_dashboard import (
    ANALYSIS_DIR,
    build_dashboard,
    render_html,
    render_markdown,
)


DOCS_DIR = ROOT / "docs"
DASHBOARD_DIR = DOCS_DIR / "dashboard"


def publish_dashboard_site(
    *,
    analysis_dir: Path = ANALYSIS_DIR,
    docs_dir: Path = DOCS_DIR,
) -> dict[str, str]:
    payload = build_dashboard(analysis_dir=analysis_dir)
    dashboard_dir = docs_dir / "dashboard"
    dashboard_dir.mkdir(parents=True, exist_ok=True)

    index_html = dashboard_dir / "index.html"
    dashboard_json = dashboard_dir / "dashboard.json"
    dashboard_md = dashboard_dir / "dashboard.md"
    root_index = docs_dir / "index.html"

    index_html.write_text(render_html(payload), encoding="utf-8")
    dashboard_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    dashboard_md.write_text(render_markdown(payload), encoding="utf-8")
    root_index.write_text(
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="0; url=./dashboard/">
  <title>BTC 1d Dashboard Redirect</title>
</head>
<body>
  <p>Redirecting to <a href="./dashboard/">dashboard</a>...</p>
</body>
</html>
""",
        encoding="utf-8",
    )

    return {
        "dashboard_index_html": str(index_html),
        "dashboard_json": str(dashboard_json),
        "dashboard_md": str(dashboard_md),
        "docs_index_html": str(root_index),
    }


def main() -> int:
    paths = publish_dashboard_site()
    print(json.dumps(paths, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
