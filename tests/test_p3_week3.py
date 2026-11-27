"""P3 Week 3 regressions: delayed repeal, reproducible scoring and evidence."""
import csv
import hashlib
import json
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from src.graph.ontology import relation_for_action, validate_edge
from src.versions import versions
from src.versions.rebuild_db import rebuild
from src.versions.week3_audit import score, run_parser, ROOT


@pytest.fixture(scope="module")
def rebuilt(tmp_path_factory):
    return rebuild(tmp_path_factory.mktemp("week3") / "qanun.db")


@pytest.mark.parametrize("article", ["22", "23", "24", "25", "26"])
def test_delayed_repeal_never_restores_current_version(article, rebuilt, monkeypatch):
    monkeypatch.setattr(versions, "DEFAULT_DB_PATH", rebuilt)
    assert versions.get_version("loi-90-11", article, "1990-04-26") is None
    assert versions.get_version("loi-90-11", article, "1997-01-12") is not None
    before = versions.get_version("loi-90-11", article, "1997-03-11")
    assert before["repealing_text_id"] == "ordonnance-97-03"
    assert before["valid_to"] == "1997-03-11"
    assert versions.get_version("loi-90-11", article, "1997-03-12") is None
    assert versions.get_version("loi-90-11", article) is None
    assert len(versions.list_versions("loi-90-11", article)) == 1
    if article == "22":
        assert "quarante quatre (44)" in before["content"]
        assert "quarante (40)" not in before["content"]


def test_gold_scope_and_parser_never_overwrite_reference():
    path = ROOT / "data/interim/amendments.json"
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    parsed = run_parser(ROOT)
    assert len(parsed) == 71
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
    with (ROOT / "data/week3/gold_51.csv").open(encoding="utf-8-sig", newline="") as f:
        gold = list(csv.DictReader(f))
    assert len(gold) == 51
    assert sum(r["expected_recoverable"] == "True" for r in gold) == 43
    assert {r["modifying_text_id"] for r in gold if r["expected_recoverable"] == "False"} == {"loi-22-16"}
    measured = score(json.loads(path.read_text()), parsed)
    assert (measured["tp"], measured["fp"], measured["fn"]) == (70, 1, 9)


def test_duplicates_and_wrong_attribution_are_not_true_positives():
    row = dict(modifying_text_id="loi-14-10", target_article="87 bis", amending_article="Art. 88", action="repeal")
    wrong = dict(row, modifying_text_id="decret-executif-15-107")
    result = score([row], [row, row, wrong])
    assert (result["tp"], result["fp"], result["fn"]) == (1, 2, 0)


def test_review_does_not_turn_missing_evidence_into_verified(rebuilt):
    with (ROOT / "data/week3/official_review.csv").open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    checked = [r for r in rows if r["week3_review_status"] == "RECHECKED_OFFICIAL_JO"]
    assert len(rows) == 28 and len(checked) == 28
    assert all(r["source_url"].startswith("https://www.joradp.dz/") and r["printed_page"].isdigit() for r in checked)
    assert sum(r["week3_review_status"] == "A_VERIFIER_WEEK3" for r in rows) == 0

    expected = {
        (r["modifying_text_id"], r["target_article"], r["provision"],
         r["printed_page"], r["source_url"])
        for r in checked
    }
    with closing(sqlite3.connect(rebuilt)) as db:
        loaded = db.execute("""
            SELECT modifying_text_id, target_article, provision,
                   CAST(source_page AS TEXT), source_url
            FROM amendment_verification
            WHERE original_status = 'A_VERIFIER_SOURCE_OFFICIELLE'
        """).fetchall()
    assert len(loaded) == 28
    assert set(loaded) == expected


def test_ontology_rejects_reversed_amendment_and_unknown_action():
    assert relation_for_action("insert") == "adds"
    assert relation_for_action("complete") == "modifies"
    assert validate_edge("Text", "repeals", "Article") == []
    assert validate_edge("Article", "mentions", "Concept") == []
    assert validate_edge("Concept", "mentions", "Article")
    assert validate_edge("Concept", "repeals", "Text")
    with pytest.raises(KeyError):
        relation_for_action("unidentified")
