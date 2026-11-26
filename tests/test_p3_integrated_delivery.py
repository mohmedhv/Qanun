"""Regressions for CSV evidence, rebuilds and the two teacher questions."""
import csv
import sqlite3
from contextlib import closing

from src.versions.load_versions import ROOT
from src.versions.load_versions import load
from src.versions.rebuild_db import rebuild
from src.versions.versions import get_version
from src.search.search_service import search


def test_csv_rows_survive_rebuild_and_reload(tmp_path):
    target = rebuild(tmp_path / "project.db")
    load(target)
    with (ROOT / "P3_Modified_Articles.csv").open(encoding="utf-8-sig", newline="") as f:
        source = list(csv.DictReader(f))
    with closing(sqlite3.connect(target)) as db, db:
        actual = db.execute("SELECT original_status,csv_status,source_url,source_page "
                            "FROM amendment_verification ORDER BY csv_row").fetchall()
        assert actual == [tuple(r[k] for k in ("original_status","verification_status","source_url","pdf_page"))
                          for r in source]
        reviewed = [r for r in source if r["original_status"] == "A_VERIFIER_SOURCE_OFFICIELLE"]
        assert len(reviewed) == 28
        assert all(r["verification_status"] == "VERIFIED_OFFICIAL_JO" and
                   r["source_url"].startswith("https://www.joradp.dz/") and
                   r["pdf_page"].isdigit() for r in reviewed)
        assert db.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert not db.execute("PRAGMA foreign_key_check").fetchall()
        assert db.execute("SELECT count(*) FROM chunks").fetchone() == (160,)


def test_cdd_historical_boundary_and_p4_lookup(monkeypatch):
    before = get_version("loi-90-11", "12", "1996-07-11")
    after = get_version("loi-90-11", "12", "1996-07-12")
    assert "par nature temporaires" not in before["content"]
    assert "par nature temporaires" in after["content"]
    assert get_version("loi-90-11", "12 bis", "1996-07-11") is None
    monkeypatch.setenv("JURIDEAZOR_SEARCH_METHOD", "bm25")
    hits = search("contrat de travail à durée déterminée", date="1997-07-01", k=30)
    assert {"12", "12 bis"} <= {x["number"] for x in hits}
    appeal = get_version("loi-90-11", "73-4", "1997-01-01")
    assert appeal["modifying_text_id"] == "ordonnance-96-21"
    assert "tribunal" in appeal["content"] and "cassation" in appeal["content"]


def test_loader_and_initializer_close_connections(tmp_path, monkeypatch):
    import src.common.init_db as schema
    import src.versions.load_versions as loader

    target = rebuild(tmp_path / "closed.db")
    connections = []
    original_connect = sqlite3.connect

    class TrackedConnection(sqlite3.Connection):
        closed = False

        def close(self):
            super().close()
            self.closed = True

    def tracked_connect(*args, **kwargs):
        kwargs["factory"] = TrackedConnection
        con = original_connect(*args, **kwargs)
        connections.append(con)
        return con

    monkeypatch.setattr(sqlite3, "connect", tracked_connect)
    schema.init_db(target)
    loader.load(target)
    assert connections
    assert all(con.closed for con in connections)
