"""Step 4 - Validate the corpus. Prints OK / ANOMALY lines. Exit code 1 if any anomaly.
Usage:  python src/structuring/validate.py
"""
import sqlite3
import sys
from pathlib import Path

DB = Path("data/db/qanun.db")
EXPECTED = 158


def main() -> int:
    con = sqlite3.connect(DB)
    rows = con.execute("SELECT sort_key, number, content, parent_title FROM articles ORDER BY sort_key").fetchall()
    problems = []

    count = len(rows)
    print(f"{'OK     ' if count == EXPECTED else 'ANOMALY'} article count = {count} (expected {EXPECTED})")
    if count != EXPECTED:
        problems.append("count")

    keys = [r[0] for r in rows]
    missing = sorted(set(range(1, EXPECTED + 1)) - set(keys))
    dups = sorted({k for k in keys if keys.count(k) > 1})
    print(f"{'OK     ' if not missing else 'ANOMALY'} missing numbers: {missing or 'none'}")
    print(f"{'OK     ' if not dups else 'ANOMALY'} duplicate numbers: {dups or 'none'}")
    problems += missing + dups

    empty = [r[1] for r in rows if len(r[2].strip()) < 20]
    print(f"{'OK     ' if not empty else 'ANOMALY'} very short/empty articles: {empty or 'none'}")
    no_title = [r[1] for r in rows if not r[3]]
    print(f"{'OK     ' if not no_title else 'ANOMALY'} articles without parent title: {no_title or 'none'}")
    dirty = [r[1] for r in rows if any(w in r[2] for w in ("Evolution", "Textes d’application", "susvisée", "Rectificatif"))]
    print(f"{'OK     ' if not dirty else 'ANOMALY'} articles with annotation leaks: {dirty or 'none'}")
    problems += empty + no_title + dirty

    print("\nRESULT:", "ALL CHECKS PASSED" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
