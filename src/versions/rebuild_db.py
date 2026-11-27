"""Rebuild the shared database in a sibling temporary directory before replacing it."""
import argparse
import os
import tempfile
from pathlib import Path

if not __package__:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.structuring import build_db, chunks
from src.versions.load_versions import load
from src.versions.versions import DEFAULT_DB_PATH


def rebuild(output=None):
    target = Path(output or DEFAULT_DB_PATH).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target.parent) as directory:
        staging = Path(directory) / "qanun.db"
        build_db.main(staging)
        chunks.main(staging)
        load(staging)
        os.replace(staging, target)
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output")
    rebuild(parser.parse_args().output)
