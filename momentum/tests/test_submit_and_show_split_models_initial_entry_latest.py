from __future__ import annotations

import sys

from tools.analysis import submit_and_show_split_models_initial_entry_latest as submit_show


def test_submit_and_show_invokes_submit_then_show(monkeypatch) -> None:
    calls: list[list[str]] = []

    def _fake_run(args: list[str], cwd, check: bool) -> None:
        assert cwd == submit_show.ROOT
        assert check is True
        calls.append(args)

    monkeypatch.setattr(submit_show.subprocess, "run", _fake_run)
    monkeypatch.setattr(submit_show.sys, "executable", "python")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/analysis/submit_and_show_split_models_initial_entry_latest.py",
            "--latest-index-path",
            "latest.json",
        ],
    )

    submit_show.main()

    assert calls == [
        [
            "python",
            "tools/pipelines/submit_split_models_initial_entry_from_latest.py",
            "--latest-index-path",
            "latest.json",
            "--submit-live",
        ],
        [
            "python",
            "tools/analysis/show_split_models_initial_entry_latest.py",
            "--latest-index-path",
            "latest.json",
        ],
    ]


def test_submit_and_show_can_emit_json(monkeypatch) -> None:
    calls: list[list[str]] = []

    def _fake_run(args: list[str], cwd, check: bool) -> None:
        calls.append(args)

    monkeypatch.setattr(submit_show.subprocess, "run", _fake_run)
    monkeypatch.setattr(submit_show.sys, "executable", "python")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tools/analysis/submit_and_show_split_models_initial_entry_latest.py",
            "--latest-index-path",
            "latest.json",
            "--json",
        ],
    )

    submit_show.main()

    assert calls[1] == [
        "python",
        "tools/analysis/show_split_models_initial_entry_latest.py",
        "--latest-index-path",
        "latest.json",
        "--json",
    ]
