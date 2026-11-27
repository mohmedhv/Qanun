from src.search.graph_ranker import hybrid_graph_rank, result_node_id


def test_result_node_id():
    assert result_node_id({
        "article_id": "loi-90-11-art-72"
    }) == "article:loi-90-11-art-72"

    assert result_node_id({
        "graph_node_id": "text:decret-legislatif-94-09"
    }) == "text:decret-legislatif-94-09"


def test_graph_ranker_adds_repealing_text():
    hybrid = [{
        "article_id": "loi-90-11-art-72",
        "cite_id": "loi-90-11-art-72",
        "score": 1.0,
    }]

    ranked = hybrid_graph_rank(
        hybrid,
        k=3,
        relation="repeals",
    )

    ids = [r["result_node_id"] for r in ranked]

    assert "article:loi-90-11-art-72" in ids
    assert "text:decret-legislatif-94-09" in ids


def test_graph_ranker_deduplicates():
    hybrid = [
        {"article_id": "loi-90-11-art-72"},
        {"article_id": "loi-90-11-art-72"},
    ]

    ranked = hybrid_graph_rank(hybrid, k=5)

    ids = [r["result_node_id"] for r in ranked]

    assert len(ids) == len(set(ids))


def test_graph_ranker_respects_k():
    hybrid = [
        {"article_id": "loi-90-11-art-4"},
        {"article_id": "loi-90-11-art-72"},
    ]

    ranked = hybrid_graph_rank(hybrid, k=3)

    assert len(ranked) <= 3


def test_graph_ranker_preserves_original_order_without_edges():
    hybrid = [
        {"article_id": "loi-90-11-art-2"},
        {"article_id": "loi-90-11-art-5"},
    ]

    ranked = hybrid_graph_rank(hybrid, k=2)

    assert [
        r["result_node_id"] for r in ranked
    ] == [
        "article:loi-90-11-art-2",
        "article:loi-90-11-art-5",
    ]
