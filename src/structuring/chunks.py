"""Week 2 - Chunking strategy for P4 (search).  See docs/chunking.md for the reasons.

RULE: one article = one chunk.  Only an article longer than MAX_CHARS is split BY PARAGRAPH,
and every part keeps the article_id, so a citation always points to the right article.

Usage:  python -m src.structuring.chunks        (run AFTER build_db.py)
Reads:  data/db/qanun.db (table articles)
Writes: table `chunks` in the same DB
"""
import json
import sqlite3
from pathlib import Path

DB = Path("data/db/qanun.db")
MAX_CHARS = 1500      # about 400 tokens in French: safe under the 512-token limit of E5 / BGE (with prefixes)


def pack(paragraphs: list[str]) -> list[list[str]]:
    """Group paragraphs into parts of at most MAX_CHARS. A paragraph is never cut in the middle."""
    intro = paragraphs[0] if paragraphs and paragraphs[0].rstrip().endswith(":") else None
    parts, cur, size = [], [], 0
    for p in paragraphs:
        if cur and size + len(p) > MAX_CHARS:
            parts.append(cur)
            cur, size = ([intro] if intro and p is not intro else []), (len(intro) if intro else 0)   # repeat the "...suivants :" intro
        cur.append(p)
        size += len(p) + 1
    parts.append(cur)
    return parts


def main(db_path=DB):
    con = sqlite3.connect(db_path)
    rows = con.execute(
        "SELECT article_id, number, parent_title, parent_chapter, parent_section, paragraphs, source_url "
        "FROM articles ORDER BY sort_key").fetchall()
    chunks = []
    for article_id, number, title, chapter, section, paras, url in rows:
        paragraphs = json.loads(paras)
        full = "\n".join(paragraphs)
        groups = [paragraphs] if len(full) <= MAX_CHARS else pack(paragraphs)
        for i, g in enumerate(groups, 1):
            text = "\n".join(g)
            context = " > ".join(x for x in (title, chapter, section) if x)
            chunks.append({
                "chunk_id": article_id if len(groups) == 1 else f"{article_id}#{i}",
                "article_id": article_id,
                "part": i, "n_parts": len(groups),
                "text": text,
                # what P4 embeds: the article number and its place in the law help the search
                "text_for_embedding": f"Loi n° 90-11, article {number} ({context})\n{text}",
                "n_chars": len(text),
                "source_url": url,
            })
    # Keep the shared schema as the only DDL source and preserve the team's JSON artifacts.
    con.execute("DELETE FROM chunks")
    con.executemany(
        "INSERT INTO chunks "
        "(chunk_id,article_id,part,n_parts,text,text_for_embedding,n_chars,source_url) "
        "VALUES (:chunk_id,:article_id,:part,:n_parts,:text,:text_for_embedding,:n_chars,:source_url)",
        chunks,
    )
    con.commit(); con.close()
    split = sorted({c["article_id"] for c in chunks if c["n_parts"] > 1})
    print(f"{len(chunks)} chunks for {len(rows)} articles; split articles: {split}; longest chunk = {max(c['n_chars'] for c in chunks)} chars")


if __name__ == "__main__":
    main()
