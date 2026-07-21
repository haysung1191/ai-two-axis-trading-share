from __future__ import annotations

import runpy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main(entry_name: str | None = None) -> int:
    if entry_name is None and len(sys.argv) < 2:
        print("usage: python _run_cached_entry.py <entry_name> [args...]", file=sys.stderr)
        return 2

    if entry_name is None:
        entry_name = sys.argv[1]
        forwarded_args = sys.argv[2:]
    else:
        forwarded_args = sys.argv[1:]
    cache_path = ROOT / "__pycache__" / f"{entry_name}.cpython-312.pyc"
    if not cache_path.exists():
        print(f"cached entry not found: {cache_path}", file=sys.stderr)
        return 2

    sys.argv = [str(ROOT / f"{entry_name}.py"), *forwarded_args]
    runpy.run_path(str(cache_path), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
