"""Week 3 graph: integrity and reproducibility of src/graph/build_graph.py."""
import csv
import filecmp

from src.graph import build_graph as bg


def test_graph_integrity():
    g = bg.build_graph()
    assert bg.check(g) == []
    entities = {d["entity"] for _, d in g.nodes(data=True)}
    assert entities == {"Text", "Article", "Version", "Concept"}
    relations = {d["relation"] for _, _, d in g.edges(data=True)}
    assert relations <= {"belongs_to", "modifies", "repeals", "adds", "applies", "cites", "mentions"}


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
        assert g.nodes[v]["version_id"] == int(v.removeprefix("version:"))
        assert g.nodes[v]["article_id"]
        assert g.nodes[v]["content"]
    assert any(g.nodes[v]["valid_to"] for v in versions)         # end dates are kept


def test_concept_mentions_are_lexical_candidates():
    g = bg.build_graph()
    concept = "concept:snmg"
    assert g.nodes[concept]["entity"] == "Concept"
    assert g.nodes[concept]["status"] == "lexical_match_unreviewed"
    assert ("article:loi-90-11-art-87", concept) in g.edges
    assert any(d["relation"] == "mentions" and d["status"] == "lexical_match_unreviewed"
               for _, _, d in g.edges(data=True))


def test_integrity_check_catches_a_version_without_its_article():
    g = bg.build_graph()
    g.remove_edges_from([(u, v, k) for u, v, k, d in g.edges(keys=True, data=True)
                         if u == "version:11" and d["relation"] == "belongs_to"])
    assert any("Version must belong to exactly one Article: version:11" in p for p in bg.check(g))


def test_csv_exports_version_identity_content_and_validity(tmp_path):
    g = bg.build_graph()
    bg.write_csv(g, tmp_path)
    with (tmp_path / "nodes.csv").open(encoding="utf-8", newline="") as f:
        nodes = {row["node_id"]: row for row in csv.DictReader(f)}
    with (tmp_path / "edges.csv").open(encoding="utf-8", newline="") as f:
        edges = list(csv.DictReader(f))
    for version_id in (6, 11, 12):
        node_id = f"version:{version_id}"
        assert nodes[node_id]["version_id"] == str(version_id)
        assert nodes[node_id]["article_id"]
        assert nodes[node_id]["content"]
        assert nodes[node_id]["valid_from"]
        assert sum(e["source"] == node_id and e["relation"] == "belongs_to" for e in edges) == 1


def test_unknown_verification_status_does_not_crash():
    assert min(["verifie_jo_officiel", "new_status_from_p3", None], key=bg.worst_first) in ("new_status_from_p3", None)
