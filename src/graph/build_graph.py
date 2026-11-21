"""Build a NetworkX multigraph from the legal SQLite tables."""
import sqlite3
import networkx as nx


def build_graph(db_path: str) -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        for row in connection.execute("SELECT * FROM texts"):
            graph.add_node(f"text:{row['text_id']}", entity="Text", **dict(row))
        for row in connection.execute("SELECT * FROM articles"):
            article_node = f"article:{row['article_id']}"
            graph.add_node(article_node, entity="Article", **dict(row))
            graph.add_edge(f"text:{row['text_id']}", article_node, relation="belongs_to")
        for row in connection.execute("SELECT * FROM relations"):
            graph.add_edge(f"text:{row['from_text_id']}", f"text:{row['to_text_id']}",
                           relation=row["relation_type"], article_number=row["to_article_number"])
    return graph

