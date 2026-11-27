from src.search.graph_aware_search import expand_with_graph


def test_original_results_preserved():
    results = [{"article_id": "loi-90-11-art-72", "cite_id": "test"}]
    expanded = expand_with_graph(results, edges=[])

    assert expanded == results
    assert expanded is not results


def test_graph_expansion():
    results = [{"article_id": "loi-90-11-art-72"}]
    edges = [{
        "source": "text:decret-legislatif-94-09",
        "target": "article:loi-90-11-art-72",
        "relation": "repeals",
        "status": "verifie_jo_officiel",
        "source_url": "https://example.org/source",
        "provision": "article 1"
    }]

    expanded = expand_with_graph(results, edges=edges)

    assert len(expanded) == 2
    assert expanded[1]["graph_node_id"] == "text:decret-legislatif-94-09"
    assert expanded[1]["relation"] == "repeals"
    assert expanded[1]["relation_status"] == "verifie_jo_officiel"
    assert expanded[1]["relation_source_url"] == "https://example.org/source"


def test_no_duplicate_neighbors():
    results = [{"article_id": "loi-90-11-art-72"}]
    edge = {
        "source": "text:decret-legislatif-94-09",
        "target": "article:loi-90-11-art-72",
        "relation": "repeals"
    }

    expanded = expand_with_graph(results, edges=[edge, edge])

    assert len(expanded) == 2


def test_max_neighbors():
    results = [{"article_id": "loi-90-11-art-4"}]
    edges = [
        {
            "source": f"text:decret-{i}",
            "target": "article:loi-90-11-art-4",
            "relation": "applies"
        }
        for i in range(5)
    ]

    expanded = expand_with_graph(
        results, edges=edges, max_neighbors=2
    )

    assert len(expanded) == 3
from src.search.graph_aware_search import expand_with_graph


def test_future_amendment_excluded():
    results = [{
        "article_id": "loi-90-11-art-73",
        "cite_id": "loi-90-11-art-73",
    }]

    expanded = expand_with_graph(
        results,
        date="1991-01-01",
        max_neighbors=10,
    )

    graph_nodes = [
        item["graph_node_id"]
        for item in expanded
        if item.get("graph_expanded")
    ]

    assert "text:loi-91-29" not in graph_nodes


def test_p3_amendment_version_match():
    results = [{
        "article_id": "loi-90-11-art-73",
        "cite_id": "loi-90-11-art-73",
    }]

    expanded = expand_with_graph(
        results,
        date="1995-01-01",
        max_neighbors=10,
    )

    matches = [
        item
        for item in expanded
        if item.get("graph_node_id") == "text:loi-91-29"
    ]

    assert len(matches) == 1
    assert matches[0]["relation"] == "modifies"
    assert matches[0]["temporal_status"] == "p3_version_match"
