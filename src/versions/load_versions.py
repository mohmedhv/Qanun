"""Load P3 into the shared P2 database in one transaction."""
import csv
import sqlite3
from contextlib import closing
from pathlib import Path

from src.common.init_db import init_db
import json

ROOT = Path(__file__).resolve().parents[2]
SEED = ROOT / "data/version_seed/p3_seed.json"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def relation_records(seed):
    """Retain Week 2 relation IDs and classify each inventoried amendment."""
    actions = {"insert": "adds", "repeal": "repeals", "modify": "modifies",
               "complete": "modifies", "term_substitution": "modifies"}
    operations = {
        (a["modifying_text_id"], "loi-90-11-art-" + a["target_article"].replace(" ", "-")): actions[a["action"]]
        for a in read(ROOT / "data/interim/amendments.json")
    }
    return [dict(row, type=operations.get((row["source_id"], row["target_id"]), row["type"]))
            for row in seed["relations"]]
from .versions import DEFAULT_DB_PATH, LEGAL_HIERARCHY


STATUS = {
    "VERIFIED_OFFICIAL_JO": "verifie_jo_officiel",
    "VERIFIED_PUBLISHED_JO_COPY": "verifie_copie_publiee",
    "A_VERIFIER_SOURCE_OFFICIELLE": "a_verifier",
}


def verification_rows():
    inventory = read(ROOT / "data/interim/amendments.json")
    index = {(a["date_signed"], a["target_article"], a["amending_article"]): a for a in inventory}
    if len(index) != len(inventory):
        raise ValueError("Duplicate inventory key")
    result = []
    with (ROOT / "P3_Modified_Articles.csv").open(encoding="utf-8-sig", newline="") as f:
        for number, row in enumerate(csv.DictReader(f), 1):
            key = row["amending_text_date"], row["law_90_11_article"], row["amending_text_article"]
            a = index.pop(key)
            result.append(dict(modifying_text_id=a["modifying_text_id"], target_article=key[1],
                               provision=key[2], csv_row=number, original_status=row["original_status"],
                               csv_status=row["verification_status"], verification_status=STATUS[row["verification_status"]],
                               source_url=row["source_url"],
                               source_page=row["pdf_page"], verification_note=row["verification_note"],
                               needs_textual_review=int(a["needs_review"])))
    if index:
        raise ValueError(f"Missing verification rows for {list(index)}")
    return result


def upsert(con, table, rows, key):
    fields = list(rows[0])
    updates = ", ".join(f"{name}=excluded.{name}" for name in fields if name not in key)
    sql = (f"INSERT INTO {table} ({','.join(fields)}) VALUES ({','.join(':'+f for f in fields)}) "
           f"ON CONFLICT ({','.join(key)}) DO UPDATE SET {updates}")
    con.executemany(sql, rows)


def load(db=DEFAULT_DB_PATH):
    seed = read(SEED)
    records = verification_rows()
    statuses = {(r["modifying_text_id"], r["target_article"]): r["verification_status"] for r in records}
    for v in seed["versions"]:
        v["verification_status"] = statuses.get((v["modifying_text_id"], v["article_number"]))
    texts = [dict(t, rank_level=LEGAL_HIERARCHY[t["type"]]) for t in seed["texts"] if t["text_id"] != "loi-90-11"]
    if not Path(db).is_file():
        raise FileNotFoundError("Build the article database before running the P3 loader")
    init_db(db)
    with closing(sqlite3.connect(Path(db).resolve().as_uri()+"?mode=rw", uri=True)) as con, con:
        con.execute("PRAGMA foreign_keys=ON")
        upsert(con, "texts", texts, ["text_id"])
        upsert(con, "relations", relation_records(seed), ["relation_id"])
        upsert(con, "versions", seed["versions"], ["version_id"])
        upsert(con, "amendment_verification", records, ["modifying_text_id", "target_article", "provision"])
    print(f"Loaded {len(records)} linked amendment verification rows")


if __name__ == "__main__":
    load()
