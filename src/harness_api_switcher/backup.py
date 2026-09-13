from __future__ import annotations

import os
import shutil
import time
from pathlib import Path

MAX_BACKUPS_PER_FILE = 10


def _prune(backups: list[Path]) -> None:
    backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    for old in backups[MAX_BACKUPS_PER_FILE:]:
        try:
            old.unlink()
        except OSError:
            pass


def backup_file(path: Path, backup_dir: Path | None = None) -> Path | None:
    """Copy *path* to a timestamped backup. Returns the backup path."""
    if not path.exists():
        return None
    stamp = time.strftime("%Y%m%d_%H%M%S")
    target_dir = backup_dir if backup_dir is not None else path.parent
    target_dir.mkdir(parents=True, exist_ok=True)
    backup = target_dir / f"{path.name}.bak.{stamp}"
    counter = 1
    while backup.exists():
        backup = target_dir / f"{path.name}.bak.{stamp}.{counter}"
        counter += 1
    shutil.copy2(path, backup)
    _prune(list(target_dir.glob(f"{path.name}.bak.*")))
    return backup


def _atomic_write(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(data, encoding="utf-8")
    os.replace(tmp, path)


def write_text(path: Path, data: str, backup_dir: Path | None = None) -> Path | None:
    backup = backup_file(path, backup_dir)
    _atomic_write(path, data)
    harden_permissions(path)
    return backup


def write_json(path: Path, data: str, backup_dir: Path | None = None) -> Path | None:
    return write_text(path, data, backup_dir)


def harden_permissions(path: Path) -> None:
    if os.name == "nt":
        return
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
