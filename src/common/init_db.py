"""Initialize the local SQLite database from schema.sql."""
from pathlib import Path
import sqlite3

from src.common.config import ROOT, resolve_path


def init_db(db_path: str | Path | None = None) -> Path:
    """Create the configured database without requiring Gemini credentials."""
    config_db = None
    config_file = ROOT / "config.yaml"
    if db_path is None and config_file.exists():
        import yaml
        with config_file.open(encoding="utf-8") as handle:
            config_db = (yaml.safe_load(handle) or {}).get("paths", {}).get("db")
    destination = Path(db_path) if db_path else resolve_path(config_db or "data/db/qanun.sqlite3")
    destination.parent.mkdir(parents=True, exist_ok=True)
    schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    with sqlite3.connect(destination) as connection:
        connection.executescript(schema)
    return destination


if __name__ == "__main__":
    print(f"Initialized database: {init_db()}")

