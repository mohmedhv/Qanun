"""Week 3 graph: integrity and reproducibility of src/graph/build_graph.py."""
import filecmp
from pathlib import Path

from src.graph import build_graph as bg


def test_graph_integrity():
    g = bg.build_graph()
    assert bg.check(g) == []
    entities = {d["entity"] for _, d in g.nodes(data=True)}
    assert entities == {"Text", "Article", "Version"}
    relations = {d["relation"] for _, _, d in g.edges(data=True)}
    assert relations <= {"belongs_to", "modifies", "repeals", "adds", "applies", "cites"}


def test_graph_is_reproducible(tmp_path):
    first, second = tmp_path / "a", tmp_path / "b"
    bg.write_csv(bg.build_graph(), first)
    bg.write_csv(bg.build_graph(), second)
    for name in ("nodes.csv", "edges.csv"):
        assert filecmp.cmp(first / name, second / name, shallow=False)


def test_cites_ignore_other_texts():
    articles = [{"number": "3", "content": "Les articles 1 à 179 de la loi n° 78-12 du 5 août 1978."},
                {"number": "5", "content": "Voir l’article 3 ci-dessus."}]
    cites, rejected = bg.extract_cites(articles)
    assert [(c["source"], c["target"]) for c in cites] == [("5", "3")]
    assert rejected and rejected[0][2] == "points to another text"


def test_every_version_has_an_article_and_real_dates():
    g = bg.build_graph()
    versions = [n for n, d in g.nodes(data=True) if d["entity"] == "Version"]
    assert versions
    for v in versions:
        links = [t for _, t, d in g.out_edges(v, data=True) if d["relation"] == "belongs_to"]
        assert len(links) == 1 and g.nodes[links[0]]["entity"] == "Article", v
        assert g.nodes[v]["valid_from"], v                       # real start of validity, not a signature date
    assert any(g.nodes[v]["valid_to"] for v in versions)         # end dates are kept


def test_unknown_verification_status_does_not_crash():
    assert min(["verifie_jo_officiel", "new_status_from_p3", None], key=bg.worst_first) in ("new_status_from_p3", None)
