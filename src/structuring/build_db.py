"""Step 3 - Load the articles into SQLite.
Usage:  python src/structuring/build_db.py
Reads:  data/interim/articles.json
Writes: data/db/qanun.db   (recreated from scratch at every run -> replayable)

NOTE: the column names below are a PROPOSAL. When P1 sends data_contract.md,
compare and rename the columns so they match it exactly.
"""
import json
import sqlite3
from pathlib import Path

DB = Path("data/db/qanun.db")
ARTICLES = Path("data/interim/articles.json")

# Text-level metadata. Fill SOURCE_URL with the real URL of the file you used.
TEXT_ID = "loi-90-11"
SOURCE_URL = "https://joradp.dz/FTP/jo-francais/1990/F1990017.pdf"

SCHEMA = """
CREATE TABLE texts (
    text_id     TEXT PRIMARY KEY,
    type        TEXT NOT NULL,          -- loi / ordonnance / decret ...
    number      TEXT NOT NULL,          -- 90-11
    title       TEXT,
    date_signed TEXT,                   -- 1990-04-21  (signature date)
    jo_number   TEXT,                   -- JO n°17 of 25/04/1990
    jo_date     TEXT,
    source_url  TEXT
);
CREATE TABLE articles (
    article_id     TEXT PRIMARY KEY,    -- loi-90-11-art-33
    text_id        TEXT NOT NULL REFERENCES texts(text_id),
    number         TEXT NOT NULL,       -- "33" or "87 bis" (kept as text)
    sort_key       INTEGER NOT NULL,    -- 33, 87 ... to sort correctly
    suffix         TEXT,                -- NULL / bis / ter
    parent_title   TEXT,
    parent_chapter TEXT,
    parent_section TEXT,
    content        TEXT NOT NULL,
    paragraphs     TEXT NOT NULL,       -- JSON list of alineas
    status         TEXT NOT NULL DEFAULT 'in_force',
    valid_from     TEXT,                -- left empty on purpose: P3 fills it (entry into force != signature)
    valid_to       TEXT,
    source_url     TEXT,
    UNIQUE (text_id, number)
);
CREATE TABLE relations (
    relation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id   TEXT NOT NULL,
    target_id   TEXT NOT NULL,
    type        TEXT NOT NULL           -- modifies / repeals / applies / cites
);
"""


def main():
    articles = json.loads(ARTICLES.read_text(encoding="utf-8"))
    DB.parent.mkdir(parents=True, exist_ok=True)
    DB.unlink(missing_ok=True)
    con = sqlite3.connect(DB)
    con.executescript(SCHEMA)
    con.execute(
        "INSERT INTO texts VALUES (?,?,?,?,?,?,?,?)",
        (TEXT_ID, "loi", "90-11", "Loi n° 90-11 du 21 avril 1990 relative aux relations de travail",
         "1990-04-21", "JO n°17", "1990-04-25", SOURCE_URL),
    )
    for a in articles:
        con.execute(
            "INSERT INTO articles (article_id,text_id,number,sort_key,suffix,parent_title,parent_chapter,"
            "parent_section,content,paragraphs,source_url) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (f"{TEXT_ID}-art-{a['number'].replace(' ', '-')}", TEXT_ID, a["number"], a["sort_key"], a["suffix"],
             a["parent_title"], a["parent_chapter"], a["parent_section"], a["content"],
             json.dumps(a["paragraphs"], ensure_ascii=False), SOURCE_URL),
        )
    con.commit()
    n = con.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    print(f"Loaded {n} articles into {DB}")
    con.close()


if __name__ == "__main__":
    main()
