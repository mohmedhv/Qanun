"""Check the SQLite database against docs/data_contract.md.

Usage (from the repo root):
  python -m src.structure.validate_articles --text LOI-90-11 --expect 158
Exit code 0 = no error, 1 = errors found (warnings do not fail).
"""
from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NUMBER_RE = re.compile(r"^([1-9]\d*)( (bis|ter|quater))?$")
ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SUFFIX_ORDER = {None: 0, "bis": 1, "ter": 2, "quater": 3}


def parse(number: str):
    m = NUMBER_RE.match(number)
    return (int(m.group(1)), SUFFIX_ORDER[m.group(3)]) if m else None


def valid_iso(value) -> bool:
    if value is None:
        return True
    if not ISO_RE.match(value):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def validate(db_path: Path, text_id: str | None, expect: int | None) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    query = "SELECT * FROM articles" + (" WHERE text_id = ?" if text_id else "")
    rows = [dict(r) for r in con.execute(query, (text_id,) if text_id else ())]
    if not rows:
        return [f"no article found{' for ' + text_id if text_id else ''}"], warnings

    by_article: dict[tuple[str, str], list[dict]] = {}
    for r in rows:
        by_article.setdefault((r["text_id"], r["article_number"]), []).append(r)

    # --- per-row checks
    for r in rows:
        tag = f"{r['text_id']}#{r['article_number']}@v{r['version_no']}"
        if parse(r["article_number"]) is None:
            errors.append(f"{tag}: article_number not normalized (digits + optional bis/ter/quater)")
        if not (r["content"] or "").strip():
            errors.append(f"{tag}: empty content")
        elif re.match(r"^\s*(art\.?|article)\s*\d", r["content"], re.I):
            warnings.append(f"{tag}: content still starts with the 'Art. N' prefix")
        if r["status"] not in ("in_force", "repealed"):
            errors.append(f"{tag}: bad status {r['status']!r}")
        for col in ("valid_from", "valid_to"):
            if not valid_iso(r[col]):
                errors.append(f"{tag}: {col} is not an ISO date ({r[col]!r})")
        if r["valid_from"] and r["valid_to"] and r["valid_to"] < r["valid_from"]:
            errors.append(f"{tag}: valid_to is before valid_from")

    # --- per-article checks (versions)
    for (t, num), versions in by_article.items():
        versions.sort(key=lambda r: r["version_no"])
        nos = [v["version_no"] for v in versions]
        if nos != list(range(1, len(nos) + 1)):
            errors.append(f"{t}#{num}: version numbers are {nos}, expected 1..{len(nos)}")
        for prev, nxt in zip(versions, versions[1:]):
            if prev["valid_to"] is None:
                errors.append(f"{t}#{num}: v{prev['version_no']} has no valid_to but v{nxt['version_no']} exists")
            elif nxt["valid_from"] and valid_iso(prev["valid_to"]) and valid_iso(nxt["valid_from"]):
                expected = (date.fromisoformat(nxt["valid_from"]) - timedelta(days=1)).isoformat()
                if prev["valid_to"] != expected:
                    errors.append(f"{t}#{num}: v{prev['version_no']}.valid_to={prev['valid_to']} "
                                  f"should be {expected} (day before v{nxt['version_no']}.valid_from)")
            if nxt["modified_by_text_id"] is None:
                errors.append(f"{t}#{num}: v{nxt['version_no']} has no modified_by_text_id")
        last = versions[-1]
        if last["status"] == "in_force" and last["valid_to"] is not None:
            errors.append(f"{t}#{num}: last version is in_force but has valid_to={last['valid_to']}")
        if last["status"] == "repealed" and last["valid_to"] is None:
            errors.append(f"{t}#{num}: repealed article has no valid_to")
        if any(v["status"] == "repealed" for v in versions[:-1]):
            errors.append(f"{t}#{num}: only the last version can be 'repealed'")

    # --- sequence of article numbers, per text
    for t in sorted({k[0] for k in by_article}):
        keys = sorted({parse(k[1]) for k in by_article if k[0] == t and parse(k[1])})
        main = sorted({k[0] for k in keys})
        if main:
            gaps = [n for n in range(main[0], main[-1] + 1) if n not in main]
            if main[0] != 1:
                warnings.append(f"{t}: first article number is {main[0]}, not 1")
            if gaps:
                errors.append(f"{t}: missing article numbers {gaps[:20]}{' ...' if len(gaps) > 20 else ''}")
        n_articles = len({k[1] for k in by_article if k[0] == t})
        print(f"{t}: {n_articles} distinct articles, {sum(len(v) for k, v in by_article.items() if k[0] == t)} rows")
        if expect is not None and text_id == t and n_articles != expect:
            errors.append(f"{t}: {n_articles} distinct articles, expected {expect}")

    # --- foreign keys and texts
    for row in con.execute("PRAGMA foreign_key_check"):
        errors.append(f"foreign key violation in table {row[0]} (rowid {row[1]})")
    for r in con.execute("SELECT text_id, rank_level, source_url FROM texts" + (" WHERE text_id = ?" if text_id else ""),
                         (text_id,) if text_id else ()):
        if not r["source_url"]:
            warnings.append(f"{r['text_id']}: texts.source_url is empty")
    return errors, warnings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", type=Path, default=ROOT / "data/db/qanun.sqlite3")
    ap.add_argument("--text", help="text_id to check, for example LOI-90-11 (default: all)")
    ap.add_argument("--expect", type=int, help="expected number of distinct articles")
    args = ap.parse_args()
    errors, warnings = validate(args.db, args.text, args.expect)
    for w in warnings:
        print("WARNING:", w)
    for e in errors:
        print("ERROR:  ", e)
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
