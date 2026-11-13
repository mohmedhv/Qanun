"""Print one article from the DB, to compare with the source (manual check).
Usage:  python src/structuring/show_article.py 33
"""
import json
import sqlite3
import sys

n = sys.argv[1]
row = sqlite3.connect("data/db/qanun.db").execute(
    "SELECT number, parent_title, parent_chapter, parent_section, paragraphs FROM articles WHERE number=?", (n,)
).fetchone()
if not row:
    sys.exit(f"Article {n} not found")
print(f"Article {row[0]}\n  {row[1]}\n  {row[2]}\n  {row[3]}")
for i, p in enumerate(json.loads(row[4]), 1):
    print(f"  [{i}] {p}")
