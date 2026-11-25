"""Load the P2 article corpus into the shared SQLite database.

Usage:  python -m src.structuring.build_db
Reads:  data/interim/articles.json and src/common/schema.sql
Writes: data/db/qanun.db (recreated from scratch; back it up before direct use)
"""
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data/db/qanun.db"
ARTICLES = ROOT / "data/interim/articles.json"
SCHEMA = ROOT / "src/common/schema.sql"

# Text-level metadata. Fill SOURCE_URL with the real URL of the file you used.
TEXT_ID = "loi-90-11"
SOURCE_URL = "https://joradp.dz/FTP/jo-francais/1990/F1990017.pdf"


def main():
    articles = json.loads(ARTICLES.read_text(encoding="utf-8"))
    DB.parent.mkdir(parents=True, exist_ok=True)
    DB.unlink(missing_ok=True)
    con = sqlite3.connect(DB)
    con.executescript(SCHEMA.read_text(encoding="utf-8"))
    con.execute(
        "INSERT INTO texts "
        "(text_id,type,number,title,date_signed,jo_number,jo_date,source_url,rank_level,language,pdf_path) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (TEXT_ID, "loi", "90-11", "Loi n° 90-11 du 21 avril 1990 relative aux relations de travail",
         "1990-04-21", "JO n°17", "1990-04-25", SOURCE_URL, 2, "fr", None),
    )
    for article in articles:
        con.execute(
            "INSERT INTO articles (article_id,text_id,number,sort_key,suffix,parent_title,parent_chapter,"
            "parent_section,content,paragraphs,source_url) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (f"{TEXT_ID}-art-{article['number'].replace(' ', '-')}", TEXT_ID, article["number"],
             article["sort_key"], article["suffix"], article["parent_title"], article["parent_chapter"],
             article["parent_section"], article["content"],
             json.dumps(article["paragraphs"], ensure_ascii=False), SOURCE_URL),
        )
    con.commit()
    count = con.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    print(f"Loaded {count} articles into {DB}")
    con.close()


if __name__ == "__main__":
    main()
