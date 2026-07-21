from __future__ import annotations

import sys

from tools.analysis import refresh_and_show_split_models_initial_entry_latest as refresh_show


def test_refresh_and_show_invokes_refresh_then_show(monkeypatch) -> None:
    calls: list[list[str]] = []

    def _fake_run(args: list[str], cwd, check: bool) -> None:
        assert cwd == refresh_show.ROOT
        assert check is True
        calls.append(args)

    monkeypatch.setattr(refresh_show.subprocess, "run", _fake_run)
    monkeypatch.setattr(refresh_show.sys, "executable", "python")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/analysis/refresh_and_show_split_models_initial_entry_latest.py",
            "--latest-index-path",
            "latest.json",
        ],
    )

    refresh_show.main()

    assert calls == [
        [
            "python",
            "tools/pipelines/submit_split_models_initial_entry_from_latest.py",
            "--latest-index-path",
            "latest.json",
        ],
        [
            "python",
            "tools/analysis/show_split_models_initial_entry_latest.py",
            "--latest-index-path",
            "latest.json",
        ],
    ]


def test_refresh_and_show_can_emit_json(monkeypatch) -> None:
    calls: list[list[str]] = []

    def _fake_run(args: list[str], cwd, check: bool) -> None:
        calls.append(args)

    monkeypatch.setattr(refresh_show.subprocess, "run", _fake_run)
    monkeypatch.setattr(refresh_show.sys, "executable", "python")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/analysis/refresh_and_show_split_models_initial_entry_latest.py",
            "--latest-index-path",
            "latest.json",
            "--json",
        ],
    )

    refresh_show.main()

    assert calls[1] == [
        "python",
        "tools/analysis/show_split_models_initial_entry_latest.py",
        "--latest-index-path",
        "latest.json",
        "--json",
    ]
