from __future__ import annotations

import subprocess
from pathlib import Path

from scripts import build_paper_package


def test_build_paper_package_invokes_all_steps(monkeypatch) -> None:
    calls: list[list[str]] = []

    def _fake_run(args: list[str], cwd: Path, check: bool):
        calls.append(args)

        class _Completed:
            returncode = 0

        return _Completed()

    monkeypatch.setattr(subprocess, "run", _fake_run)
    monkeypatch.setattr(build_paper_package.sys, "executable", "python")
    monkeypatch.setattr(build_paper_package.sys, "argv", ["build_paper_package.py"])

    build_paper_package.main()

    assert len(calls) == 3
    assert calls[0][1].endswith("export_paper_results.py")
    assert calls[1][1].endswith("build_paper_figures.py")
    assert calls[2][1].endswith("assemble_paper_manuscript.py")
