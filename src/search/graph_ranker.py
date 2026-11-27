"""Rank hybrid results together with their graph neighbours.

Experimental graph-only reranking. The original search is unchanged.
"""

from src.search.graph_aware_search import expand_with_graph


def result_node_id(result):
    """Give every result one comparable graph identifier."""
    if result.get("graph_node_id"):
        return result["graph_node_id"]

    article_id = result.get("article_id")

    if article_id:
        return "article:" + article_id.removeprefix("article:")

    return None


def hybrid_graph_rank(
    hybrid_results,
    k=5,
    date=None,
    relation=None,
):
    """Interleave each hybrid article with its graph neighbours."""

    if not isinstance(k, int) or isinstance(k, bool) or k < 1:
        raise ValueError("k must be a positive integer")

    ranked = []
    seen = set()

    for result in hybrid_results:
        seed = dict(result)

        candidates = expand_with_graph(
            [seed],
            date=date,
            max_neighbors=k,
        )

        for candidate in candidates:
            if candidate.get("graph_expanded"):
                if relation and candidate.get("relation") != relation:
                    continue

            node_id = result_node_id(candidate)

            if not node_id or node_id in seen:
                continue

            seen.add(node_id)

            candidate = dict(candidate)
            candidate["result_node_id"] = node_id
            candidate["retrieval_method"] = (
                "hybrid_graph"
                if candidate.get("graph_expanded")
                else "hybrid"
            )

            ranked.append(candidate)

            if len(ranked) >= k:
                return ranked

    return ranked
