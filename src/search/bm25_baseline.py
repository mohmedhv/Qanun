"""Simple SQLite-backed BM25 article retrieval baseline."""
import sqlite3
from pathlib import Path
from rank_bm25 import BM25Okapi
from src.common.config import ROOT


def search(question: str, date: str | None = None, k: int = 5, db_path: str | Path | None = None):
    """Return up to k article rows ranked by BM25; date filters validity."""
    path = Path(db_path) if db_path else ROOT / "data/db/qanun.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        if date:
            rows = connection.execute(
                "SELECT * FROM articles WHERE (valid_from IS NULL OR valid_from <= ?) "
                "AND (valid_to IS NULL OR valid_to > ?) AND status = 'in_force'", (date, date)
            ).fetchall()
        else:
            rows = connection.execute("SELECT * FROM articles WHERE status = 'in_force'").fetchall()
    if not rows:
        return []
    tokenize = lambda value: value.lower().split()
    bm25 = BM25Okapi([tokenize(row["content"]) for row in rows])
    scores = bm25.get_scores(tokenize(question))
    return [dict(row) for _, row in sorted(zip(scores, rows), key=lambda pair: pair[0], reverse=True)[:k]]

