"""Development-only evaluation of Hybrid versus Hybrid + Graph."""

import csv
import os
from pathlib import Path

os.environ["JURIDEAZOR_SEARCH_METHOD"] = "hybrid"

from src.search.search_service import search
from src.search.graph_ranker import hybrid_graph_rank, result_node_id


def hit_at_k(ranked_ids, expected_id, k):
    return int(expected_id in ranked_ids[:k])


def evaluate():
    with open(
        "eval/p4/questions.csv",
        encoding="utf-8-sig",
        newline=""
    ) as f:
        questions = [
            row for row in csv.DictReader(f)
            if row["split"] == "dev"
        ]

    rows = []

    for q in questions:
        expected = "article:" + q["expected_cite_id"]

        hybrid = search(q["question"], k=5)
        graph = hybrid_graph_rank(hybrid, k=5)

        hybrid_ids = [
            result_node_id(r) for r in hybrid
        ]
        graph_ids = [
            result_node_id(r) for r in graph
        ]

        h3 = hit_at_k(hybrid_ids, expected, 3)
        g3 = hit_at_k(graph_ids, expected, 3)

        h5 = hit_at_k(hybrid_ids, expected, 5)
        g5 = hit_at_k(graph_ids, expected, 5)

        rows.append({
            "question_id": q["question_id"],
            "expected_node_id": expected,
            "hybrid_top3": ";".join(hybrid_ids[:3]),
            "graph_top3": ";".join(graph_ids[:3]),
            "hybrid_hit3": h3,
            "graph_hit3": g3,
            "hybrid_recall5": h5,
            "graph_recall5": g5,
            "outcome": (
                "improved" if g3 > h3
                else "worsened" if g3 < h3
                else "unchanged"
            ),
        })

        print(
            q["question_id"],
            "| Hybrid Hit@3:", h3,
            "| Graph Hit@3:", g3,
            "|", rows[-1]["outcome"]
        )

    output = Path("eval/p4/graph_dev_comparison.csv")

    with output.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    n = len(rows)

    print("\nDEV SUMMARY")
    print("Hybrid Hit@3:", sum(r["hybrid_hit3"] for r in rows) / n)
    print("Graph Hit@3:", sum(r["graph_hit3"] for r in rows) / n)
    print("Hybrid Recall@5:", sum(r["hybrid_recall5"] for r in rows) / n)
    print("Graph Recall@5:", sum(r["graph_recall5"] for r in rows) / n)
    print("Saved:", output)


if __name__ == "__main__":
    evaluate()
