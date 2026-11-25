"""Validate article numbering and version dates against the shared schema.

Usage (from the repository root):
  python -m src.structure.validate_articles --text loi-90-11 --expect 158
Exit code 0 means no errors; warnings do not fail validation.
"""
from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NUMBER_RE = re.compile(r"^([1-9]\d*)(?:\s*(?:bis|ter|quater)|-\d+(?:\s*(?:bis|ter|quater))?)?$", re.I)
ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse(number: str) -> int | None:
    match = NUMBER_RE.fullmatch(str(number).strip())
    return int(match.group(1)) if match else None


def valid_iso(value) -> bool:
    if value is None:
        return True
    if not isinstance(value, str) or not ISO_RE.fullmatch(value):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def _columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}


def _check_dates(errors: list[str], tag: str, record: dict, columns: tuple[str, ...]) -> None:
    for column in columns:
        value = record[column]
        if not valid_iso(value):
            errors.append(f"{tag}: {column} is not an ISO date ({value!r})")
    start, end = record.get("valid_from"), record.get("valid_to")
    if start and end and valid_iso(start) and valid_iso(end) and end < start:
        errors.append(f"{tag}: valid_to is before valid_from")


def validate(db_path: Path, text_id: str | None, expect: int | None) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        article_columns = _columns(connection, "articles")
        required_article_columns = {"article_id", "text_id", "number", "sort_key", "content", "status", "valid_from", "valid_to"}
        missing_article_columns = sorted(required_article_columns - article_columns)
        if missing_article_columns:
            return [f"articles table is missing columns: {', '.join(missing_article_columns)}"], warnings

        query = "SELECT * FROM articles" + (" WHERE text_id = ?" if text_id else "")
        params = (text_id,) if text_id else ()
        article_rows = [dict(row) for row in connection.execute(query, params)]
        if not article_rows:
            return [f"no article found{' for ' + text_id if text_id else ''}"], warnings

        grouped: dict[tuple[str, str], list[dict]] = {}
        mains_by_text: dict[str, set[int]] = {}
        seen_ids: set[str] = set()
        for row in article_rows:
            number = str(row["number"])
            tag = f"{row['text_id']}#{number}"
            if row["article_id"] in seen_ids:
                errors.append(f"{tag}: duplicate article_id {row['article_id']!r}")
            seen_ids.add(row["article_id"])
            main_number = parse(number)
            if main_number is None:
                errors.append(f"{tag}: number is not normalized")
            else:
                mains_by_text.setdefault(row["text_id"], set()).add(main_number)
                if row["sort_key"] != main_number:
                    errors.append(f"{tag}: sort_key={row['sort_key']} should be {main_number}")
            grouped.setdefault((row["text_id"], number), []).append(row)
            if not (row["content"] or "").strip():
                errors.append(f"{tag}: empty content")
            if row["status"] not in ("in_force", "repealed"):
                errors.append(f"{tag}: bad status {row['status']!r}")
            _check_dates(errors, tag, row, ("valid_from", "valid_to"))

        for (parent_text, number), rows in grouped.items():
            if len(rows) > 1:
                errors.append(f"{parent_text}#{number}: duplicate article number ({len(rows)} rows)")

        for parent_text, mains in mains_by_text.items():
            if not mains:
                continue
            missing = [value for value in range(1, max(mains) + 1) if value not in mains]
            if min(mains) != 1:
                warnings.append(f"{parent_text}: first article number is {min(mains)}, not 1")
            if missing:
                errors.append(f"{parent_text}: missing article numbers {missing[:20]}{' ...' if len(missing) > 20 else ''}")
            count = len({number for (owner, number) in grouped if owner == parent_text})
            row_count = sum(len(rows) for (owner, _), rows in grouped.items() if owner == parent_text)
            print(f"{parent_text}: {count} distinct articles, {row_count} rows")
            if expect is not None and text_id == parent_text and count != expect:
                errors.append(f"{parent_text}: {count} distinct articles, expected {expect}")

        if "versions" not in {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}:
            errors.append("versions table is missing; P3 schema is not available")
        else:
            version_columns = _columns(connection, "versions")
            required_version_columns = {"article_id", "valid_from", "valid_to"}
            missing_version_columns = sorted(required_version_columns - version_columns)
            if missing_version_columns:
                errors.append(
                    "version continuity not checked; versions table is missing columns: "
                    + ", ".join(missing_version_columns)
                )
            else:
                optional_version_columns = {"version_number", "content", "status"} & version_columns
                selected_columns = ["article_id", "valid_from", "valid_to", *sorted(optional_version_columns)]
                version_rows = [dict(row) for row in connection.execute(
                    "SELECT " + ", ".join(selected_columns) + " FROM versions"
                )]
                by_article: dict[str, list[dict]] = {}
                for row in version_rows:
                    tag = f"{row['article_id']}@v{row.get('version_number', '?')}"
                    _check_dates(errors, tag, row, ("valid_from", "valid_to"))
                    if "content" in row and not (row["content"] or "").strip():
                        errors.append(f"{tag}: empty content")
                    if "status" in row and row["status"] not in ("in_force", "repealed"):
                        errors.append(f"{tag}: bad status {row['status']!r}")
                    by_article.setdefault(row["article_id"], []).append(row)
                for article_id, versions in by_article.items():
                    if "version_number" in optional_version_columns:
                        versions.sort(key=lambda row: row["version_number"] or 0)
                        sequence = [row["version_number"] for row in versions]
                        if sequence != list(range(1, len(sequence) + 1)):
                            errors.append(f"{article_id}: version numbers are {sequence}, expected 1..{len(sequence)}")
                    else:
                        versions.sort(key=lambda row: (row["valid_from"] is not None, row["valid_from"] or ""))
                    for previous, following in zip(versions, versions[1:]):
                        if previous["valid_to"] is None:
                            errors.append(f"{article_id}: an earlier version has no valid_to")
                        elif following["valid_from"] and valid_iso(previous["valid_to"]) and valid_iso(following["valid_from"]):
                            expected_end = (date.fromisoformat(following["valid_from"]) - timedelta(days=1)).isoformat()
                            if previous["valid_to"] != expected_end:
                                errors.append(
                                    f"{article_id}: valid_to={previous['valid_to']} should be {expected_end} "
                                    "(day before the next valid_from)"
                                )
                    if "status" in optional_version_columns:
                        if any(row["status"] == "repealed" for row in versions[:-1]):
                            errors.append(f"{article_id}: only the last version can be 'repealed'")

        for row in connection.execute("PRAGMA foreign_key_check"):
            errors.append(f"foreign key violation in table {row[0]} (rowid {row[1]})")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--db", type=Path, default=ROOT / "data/db/qanun.db")
    parser.add_argument("--text", help="text_id to check, for example loi-90-11 (default: all)")
    parser.add_argument("--expect", type=int, help="expected number of distinct articles")
    args = parser.parse_args()
    try:
        errors, warnings = validate(args.db, args.text, args.expect)
    except sqlite3.Error as exc:
        print(f"ERROR: {exc}")
        return 1
    for warning in warnings:
        print("WARNING:", warning)
    for error in errors:
        print("ERROR:  ", error)
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
