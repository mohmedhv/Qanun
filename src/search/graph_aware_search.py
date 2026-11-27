"""Graph-aware expansion with conservative temporal filtering."""

import csv
import sqlite3
from datetime import date as date_type
from pathlib import Path

GRAPH_DIR = Path("data/graph")
DB_PATH = Path("data/db/qanun.db")

RELATIONS = {
    "modifies", "adds", "repeals", "applies", "cites"
}


def read_csv(path):
    with Path(path).open(
        encoding="utf-8-sig", newline=""
    ) as file:
        return list(csv.DictReader(file))


def load_graph_edges(path=None):
    return read_csv(path or GRAPH_DIR / "edges.csv")


def load_graph_nodes(path=None):
    rows = read_csv(path or GRAPH_DIR / "nodes.csv")
    return {row["node_id"]: row for row in rows}


def _normalize_date(value):
    if value is None:
        return None
    if isinstance(value, date_type):
        return value.isoformat()
    return date_type.fromisoformat(str(value)).isoformat()


def _p3_modification_check(article_id, text_id, date):
    """Return True/False for tracked P3 articles, None if untracked."""

    if not DB_PATH.exists():
        return None

    with sqlite3.connect(DB_PATH) as con:
        rows = con.execute(
            """
            SELECT valid_from, valid_to, modifying_text_id
            FROM versions
            WHERE article_id = ?
            """,
            (article_id,),
        ).fetchall()

    if not rows:
        return None

    return any(
        modifying == text_id
        and start is not None
        and start <= date
        and (end is None or date <= end)
        for start, end, modifying in rows
    )


def expand_with_graph(
    results,
    edges=None,
    max_neighbors=10,
    date=None,
    nodes=None,
):
    """Append graph evidence without changing original search results."""

    if not isinstance(max_neighbors, int) or max_neighbors < 0:
        raise ValueError("max_neighbors must be non-negative")

    requested_date = _normalize_date(date)

    expanded = [dict(result) for result in results]

    if max_neighbors == 0:
        return expanded

    edges = load_graph_edges() if edges is None else edges
    nodes = load_graph_nodes() if nodes is None else nodes

    seeds = {
        f"article:{result['article_id']}"
        for result in results
        if result.get("article_id")
    }

    seen = set(seeds)
    added = 0

    for edge in edges:
        relation = edge.get("relation")

        if relation not in RELATIONS:
            continue

        source = edge.get("source", "")
        target = edge.get("target", "")

        if target in seeds:
            neighbor = source
            direction = "incoming"
            article_node = target
        elif source in seeds:
            neighbor = target
            direction = "outgoing"
            article_node = source
        else:
            continue

        if not neighbor or neighbor in seen:
            continue

        node = nodes.get(neighbor, {})
        temporal_status = "not_date_filtered"

        if requested_date is not None:
            signed = node.get("date_signed")

            # Exclude evidence signed in the future.
            if signed and signed > requested_date:
                continue

            temporal_status = "effective_date_unverified"

            # Use P3 for a tracked amendment where possible.
            if relation == "modifies" and neighbor.startswith("text:"):
                check = _p3_modification_check(
                    article_node.removeprefix("article:"),
                    neighbor.removeprefix("text:"),
                    requested_date,
                )

                if check is False:
                    continue

                if check is True:
                    temporal_status = "p3_version_match"

        seen.add(neighbor)

        expanded.append({
            "graph_node_id": neighbor,
            "graph_entity": node.get("entity"),
            "graph_label": node.get("label"),
            "graph_date_signed": node.get("date_signed"),
            "relation": relation,
            "relation_direction": direction,
            "relation_source": source,
            "relation_target": target,
            "relation_status": edge.get("status"),
            "relation_source_url": edge.get("source_url"),
            "relation_provision": edge.get("provision"),
            "temporal_status": temporal_status,
            "graph_expanded": True,
        })

        added += 1

        if added >= max_neighbors:
            break

    return expanded
