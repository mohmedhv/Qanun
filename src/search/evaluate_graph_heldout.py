"""Week 3 held-out evaluation using the frozen graph ranker."""

import csv
import os
from pathlib import Path

os.environ["JURIDEAZOR_SEARCH_METHOD"] = "hybrid"

from src.search.search_service import search
from src.search.graph_ranker import hybrid_graph_rank, result_node_id

BASE = Path("eval/p4")


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def evaluate_question(q):
    expected = "article:" + q["expected_cite_id"]

    hybrid = search(q["question"], k=5)
    graph = hybrid_graph_rank(hybrid, k=5)

    h_ids = [result_node_id(r) for r in hybrid]
    g_ids = [result_node_id(r) for r in graph]

    h3 = int(expected in h_ids[:3])
    g3 = int(expected in g_ids[:3])
    h5 = int(expected in h_ids[:5])
    g5 = int(expected in g_ids[:5])

    return {
        "question_id": q["question_id"],
        "split": q["split"],
        "expected_node_id": expected,
        "hybrid_top3": ";".join(h_ids[:3]),
        "graph_top3": ";".join(g_ids[:3]),
        "hybrid_hit3": h3,
        "graph_hit3": g3,
        "hybrid_recall5": h5,
        "graph_recall5": g5,
        "outcome": (
            "improved" if (g3, g5) > (h3, h5)
            else "worsened" if (g3, g5) < (h3, h5)
            else "unchanged"
        ),
    }


questions = read_csv(BASE / "questions.csv")
dev = read_csv(BASE / "graph_dev_comparison.csv")

for row in dev:
    row["split"] = "dev"

test_questions = [
    q for q in questions if q["split"] == "test"
]

assert len(dev) == 10
assert len(test_questions) == 10

print("FROZEN HELD-OUT EVALUATION")

test = []

for q in test_questions:
    result = evaluate_question(q)
    test.append(result)

    print(
        result["question_id"],
        "| Hybrid:", result["hybrid_hit3"],
        "| Graph:", result["graph_hit3"],
        "|", result["outcome"]
    )

all_rows = dev + test

output = BASE / "graph_week3_per_question.csv"

columns = [
    "question_id", "split", "expected_node_id",
    "hybrid_top3", "graph_top3",
    "hybrid_hit3", "graph_hit3",
    "hybrid_recall5", "graph_recall5",
    "outcome",
]

with output.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=columns)
    writer.writeheader()
    writer.writerows(all_rows)

print("\nSUMMARY")

for split in ["dev", "test", "all"]:
    subset = [
        r for r in all_rows
        if split == "all" or r["split"] == split
    ]

    n = len(subset)

    print("\n", split.upper(), ":", n, "questions")

    for metric in [
        "hybrid_hit3", "graph_hit3",
        "hybrid_recall5", "graph_recall5"
    ]:
        value = sum(int(r[metric]) for r in subset) / n
        print(metric, ":", round(value, 4))

    for status in ["improved", "worsened", "unchanged"]:
        print(
            status, ":",
            sum(r["outcome"] == status for r in subset)
        )

print("\nREPORT SAVED:", output)
