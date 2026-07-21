from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
import time


LOCK_ENV_VAR = "MOMENTUM_OP_CONV_LOCK_HELD"


def _lock_dir(repo_root: Path) -> Path:
    return repo_root / "output" / "split_models_operational_conversion.lockdir"


def _owner_file(lock_dir: Path) -> Path:
    return lock_dir / "owner.json"


def _read_lock_pid(lock_dir: Path) -> int | None:
    try:
        raw = _owner_file(lock_dir).read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None

    if not raw:
        return None

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None

    pid = payload.get("pid")
    if isinstance(pid, int):
        return pid
    if isinstance(pid, str) and pid.isdigit():
        return int(pid)
    return None


def _pid_is_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _write_owner(lock_dir: Path) -> None:
    payload = {
        "pid": os.getpid(),
        "created_at": time.time(),
    }
    _owner_file(lock_dir).write_text(json.dumps(payload), encoding="utf-8")


def _clear_lock_dir(lock_dir: Path) -> None:
    try:
        _owner_file(lock_dir).unlink()
    except FileNotFoundError:
        pass
    try:
        lock_dir.rmdir()
    except FileNotFoundError:
        pass


@contextmanager
def operational_conversion_lock(repo_root: Path, *, timeout_seconds: float = 30.0, poll_seconds: float = 0.1):
    if os.environ.get(LOCK_ENV_VAR) == "1":
        yield False
        return

    lock_dir = _lock_dir(repo_root)
    lock_dir.parent.mkdir(parents=True, exist_ok=True)

    start = time.monotonic()
    while True:
        try:
            lock_dir.mkdir()
            _write_owner(lock_dir)
            break
        except FileExistsError:
            lock_pid = _read_lock_pid(lock_dir)
            if lock_pid is None or not _pid_is_running(lock_pid):
                try:
                    _clear_lock_dir(lock_dir)
                except PermissionError:
                    if time.monotonic() - start >= timeout_seconds:
                        raise TimeoutError(f"Timed out waiting to clear stale lock: {lock_dir}")
                    time.sleep(poll_seconds)
                    continue
                continue
            if time.monotonic() - start >= timeout_seconds:
                raise TimeoutError(f"Timed out waiting for lock: {lock_dir}")
            time.sleep(poll_seconds)

    try:
        yield True
    finally:
        _clear_lock_dir(lock_dir)
