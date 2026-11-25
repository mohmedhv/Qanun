"""Build a NetworkX multigraph from the legal SQLite tables."""
import sqlite3
import networkx as nx


def build_graph(db_path: str) -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        text_rows = connection.execute("SELECT * FROM texts").fetchall()
        article_rows = connection.execute("SELECT * FROM articles").fetchall()
        text_ids = {row["text_id"] for row in text_rows}
        article_ids = {row["article_id"] for row in article_rows}

        for row in text_rows:
            graph.add_node(f"text:{row['text_id']}", entity="Text", **dict(row))
        for row in article_rows:
            article_node = f"article:{row['article_id']}"
            graph.add_node(article_node, entity="Article", **dict(row))
            graph.add_edge(f"text:{row['text_id']}", article_node, relation="belongs_to")

        def node_id(identifier: str) -> str:
            if identifier in article_ids:
                return f"article:{identifier}"
            if identifier in text_ids:
                return f"text:{identifier}"
            return identifier

        for row in connection.execute("SELECT * FROM relations"):
            graph.add_edge(node_id(row["source_id"]), node_id(row["target_id"]), relation=row["type"])
    return graph

