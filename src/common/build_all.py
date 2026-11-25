"""Run the shared database build in contract order with per-step results."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data/db/qanun.db"
BACKUP = ROOT / "data/db/qanun.db.bak"


def _run_module(module: str) -> tuple[bool, str]:
    result = subprocess.run(
        [sys.executable, "-m", module],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    output = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
    if result.returncode:
        return False, output or f"module exited with code {result.returncode}"
    return True, output


def _build_db() -> tuple[bool, str]:
    if DB.exists():
        if BACKUP.exists():
            return False, f"refusing to overwrite existing backup: {BACKUP}"
        try:
            shutil.copy2(DB, BACKUP)
        except OSError as exc:
            return False, f"database backup failed; build_db was not run: {exc}"
        backup_message = f"Backed up existing database to {BACKUP}."
    else:
        backup_message = "No existing database to back up."

    succeeded, output = _run_module("src.structuring.build_db")
    return succeeded, "\n".join(part for part in (backup_message, output) if part)


def _run_p3_loader() -> tuple[bool, str]:
    module = os.getenv("QANUN_P3_VERSIONS_LOADER", "").strip()
    if not module:
        return False, (
            "P3 versions loader is not present/configured. Set QANUN_P3_VERSIONS_LOADER "
            "to the module supplied by P3; see docs/contract_open_questions.md."
        )
    return _run_module(module)


def main() -> int:
    steps: list[tuple[str, Callable[[], tuple[bool, str]]]] = [
        ("build_db", _build_db),
        ("chunks", lambda: _run_module("src.structuring.chunks")),
        ("P3 versions loader", _run_p3_loader),
        ("src.structuring.validate", lambda: _run_module("src.structuring.validate")),
        ("src.versions.validate_versions", lambda: _run_module("src.versions.validate_versions")),
    ]
    failed = False
    for label, action in steps:
        try:
            succeeded, output = action()
        except Exception as exc:
            succeeded, output = False, f"{type(exc).__name__}: {exc}"
        status = "OK" if succeeded else "FAILED"
        print(f"[{status}] {label}")
        if output:
            print(output)
        failed |= not succeeded
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
