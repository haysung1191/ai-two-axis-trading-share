from __future__ import annotations

import os
from pathlib import Path
import sys
import webbrowser


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


DASHBOARD_HTML = REPO_ROOT / "output" / "split_models_operational_conversion_dashboard" / "dashboard.html"


def main() -> None:
    if not DASHBOARD_HTML.exists():
        raise SystemExit(f"Dashboard file not found: {DASHBOARD_HTML}")

    dashboard_uri = DASHBOARD_HTML.resolve().as_uri()
    opened = webbrowser.open(dashboard_uri)

    print(f"dashboard_file={DASHBOARD_HTML.relative_to(REPO_ROOT)}")
    print(f"dashboard_uri={dashboard_uri}")
    print(f"opened={str(bool(opened)).lower()}")


if __name__ == "__main__":
    main()
