"""Find graph candidates from explicit legal-article questions.

This is candidate generation, not final retrieval ranking.
"""

import re

from src.search.article_detection import article_to_graph_node
from src.search.graph_aware_search import (
    load_graph_edges,
    load_graph_nodes,
)


def detect_relation(question):
    text = question.casefold()

    patterns = {
        "repeals": r"\b(?:abroge|abroger|abrogation)\b",
        "adds": r"\b(?:ajoute|ajouter|addition)\b",
        "modifies": r"\b(?:modifie|modifier|modification)\b",
        "applies": r"\b(?:appliquant|applique|application)\b",
    }

    for relation, pattern in patterns.items():
        if re.search(pattern, text):
            return relation

    return None


def extract_signed_date(question):
    match = re.search(
        r"\bsign[ée]\s+le\s+(\d{4}-\d{2}-\d{2})\b",
        question,
        flags=re.IGNORECASE,
    )
    return match.group(1) if match else None


def graph_candidates(question, edges=None, nodes=None):
    """Return graph-linked texts without using expected answers."""

    article_node = article_to_graph_node(question)
    relation = detect_relation(question)
    signed_date = extract_signed_date(question)

    if not article_node or not relation:
        return []

    edges = load_graph_edges() if edges is None else edges
    nodes = load_graph_nodes() if nodes is None else nodes

    candidates = []
    seen = set()

    for edge in edges:
        if edge.get("target") != article_node:
            continue

        if edge.get("relation") != relation:
            continue

        source = edge.get("source", "")

        if not source.startswith("text:"):
            continue

        node = nodes.get(source)

        if not node:
            continue

        if signed_date and node.get("date_signed") != signed_date:
            continue

        if source in seen:
            continue

        seen.add(source)

        candidates.append({
            "graph_node_id": source,
            "text_id": source.removeprefix("text:"),
            "article_id": article_node.removeprefix("article:"),
            "relation": relation,
            "date_signed": node.get("date_signed"),
            "relation_status": edge.get("status"),
            "source_url": edge.get("source_url"),
            "graph_expanded": True,
        })

    return candidates
