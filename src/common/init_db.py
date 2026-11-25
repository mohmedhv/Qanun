"""Initialize the local SQLite database from schema.sql."""
from pathlib import Path
import sqlite3

from src.common.config import ROOT


def init_db(db_path: str | Path | None = None) -> Path:
    """Create the shared-schema database without requiring LLM credentials."""
    destination = Path(db_path) if db_path else ROOT / "data/db/qanun.db"
    destination.parent.mkdir(parents=True, exist_ok=True)
    schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    with sqlite3.connect(destination) as connection:
        connection.executescript(schema)
        text_columns = {row[1] for row in connection.execute("PRAGMA table_info(texts)")}
        if "rank_level" not in text_columns:
            connection.execute(
                "ALTER TABLE texts ADD COLUMN rank_level INTEGER CHECK (rank_level BETWEEN 1 AND 5)"
            )
        if "language" not in text_columns:
            connection.execute("ALTER TABLE texts ADD COLUMN language TEXT NOT NULL DEFAULT 'fr'")
        if "pdf_path" not in text_columns:
            connection.execute("ALTER TABLE texts ADD COLUMN pdf_path TEXT")
        connection.execute(
            "UPDATE texts SET rank_level = CASE "
            "WHEN lower(type) IN ('loi', 'ordonnance', 'law', 'ordinance') THEN 2 "
            "WHEN lower(type) LIKE 'decret%' OR lower(type) = 'decree' THEN 3 "
            "WHEN lower(type) IN ('arrete', 'order') THEN 4 "
            "WHEN lower(type) = 'circulaire' THEN 5 "
            "WHEN lower(type) = 'constitution' THEN 1 ELSE rank_level END "
            "WHERE rank_level IS NULL OR lower(type) IN ('loi', 'ordonnance', 'law', 'ordinance')"
        )
    return destination


if __name__ == "__main__":
    print(f"Initialized database: {init_db()}")

