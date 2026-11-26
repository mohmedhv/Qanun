"""Baseline-vs-expansion evaluation on eval/questions.csv.

Run: python -m src.search.evaluate_expanded
Tune on dev only. Treat test as held out.
"""
import csv
import json
from pathlib import Path
from .search_service import load_documents
from .bm25_search import BM25Index
from .semantic_search import E5Index
from .hybrid_search import reciprocal_rank_fusion
from .legal_query_expansion import expand_queries, expanded_query_text

QUESTIONS = Path("eval/questions.csv")
OUT = Path("eval/results/query_expansion_comparison.csv")
SUMMARY = Path("eval/results/query_expansion_metrics.json")

def dedupe(ranked, k=None):
    seen, out = set(), []
    for doc, score in ranked:
        if doc["cite_id"] not in seen:
            seen.add(doc["cite_id"])
            out.append((doc, score))
        if k is not None and len(out) >= k:
            break
    return out

def get_rank(ranking, expected):
    return next((i for i, (d, _) in enumerate(ranking, 1)
                 if d["cite_id"] == expected), None)

def measure(rows, split, condition, method):
    subset = [r for r in rows if r["split"] == split]
    ranks = [r[f"{condition}_{method}_rank"] for r in subset]
    n = len(ranks)
    if not n:
        return {"n": 0, "recall@1": None, "recall@3": None,
                "recall@5": None, "mrr@5": None}
    return {
        "n": n,
        "recall@1": sum(x is not None and x <= 1 for x in ranks) / n,
        "recall@3": sum(x is not None and x <= 3 for x in ranks) / n,
        "recall@5": sum(x is not None and x <= 5 for x in ranks) / n,
        "mrr@5": sum(1/x if x is not None and x <= 5 else 0 for x in ranks) / n,
    }

def main():
    with QUESTIONS.open(encoding="utf-8-sig", newline="") as f:
        questions = list(csv.DictReader(f))
    required = {"question_id", "split", "question", "expected_cite_id"}
    if not questions or not required.issubset(questions[0]):
        raise ValueError(f"questions.csv must contain {sorted(required)}")
    if any(q["split"] not in {"dev", "test"} for q in questions):
        raise ValueError("Invalid or missing dev/test split")
    if len({q["question_id"] for q in questions}) != len(questions):
        raise ValueError("Duplicate question IDs")

    docs = load_documents()
    if not docs:
        raise ValueError("No documents loaded")
    bm, e5 = BM25Index(docs), E5Index(docs)
    e5.search(questions[0]["question"], k=1)  # fail before writing partial output

    rows = []
    for q in questions:
        original = q["question"]
        variants = expand_queries(original)
        b0 = dedupe(bm.search(original, k=len(docs)))
        e0 = dedupe(e5.search(original, k=len(docs)))
        h0 = dedupe(reciprocal_rank_fusion(b0, e0, k=len(docs)))

        # BM25 uses a concatenated query. E5 ranks each query separately and
        # fuses the article rankings. Hybrid then fuses expanded BM25 and E5.
        b1 = dedupe(bm.search(expanded_query_text(original), k=len(docs)))
        e_lists = [dedupe(e5.search(v, k=len(docs))) for v in variants]
        e1 = dedupe(reciprocal_rank_fusion(*e_lists, k=len(docs)))
        h1 = dedupe(reciprocal_rank_fusion(b1, e1, k=len(docs)))

        row = {
            "question_id": q["question_id"], "split": q["split"],
            "question": original, "expected_cite_id": q["expected_cite_id"],
            "generated_queries": " || ".join(variants),
        }
        for condition, rankings in (
            ("baseline", {"bm25": b0, "e5": e0, "hybrid": h0}),
            ("expanded", {"bm25": b1, "e5": e1, "hybrid": h1}),
        ):
            for method, ranking in rankings.items():
                row[f"{condition}_{method}_rank"] = get_rank(ranking, q["expected_cite_id"])
                row[f"{condition}_{method}_top5"] = ";".join(d["cite_id"] for d, _ in ranking[:5])
        rows.append(row)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    summary = {
        "dataset": str(QUESTIONS), "corpus_chunks": len(docs),
        "model": e5.model_name, "max_generated_variants": 4,
        "warning": "Tune on dev only; test is held out. This evaluates P2 corpus, not P3 dated retrieval.",
        "metrics": {
            split: {
                condition: {method: measure(rows, split, condition, method)
                            for method in ("bm25", "e5", "hybrid")}
                for condition in ("baseline", "expanded")
            } for split in ("dev", "test")
        }
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary["metrics"], ensure_ascii=False, indent=2))
    print("Wrote:", OUT)
    print("Wrote:", SUMMARY)
    return rows

if __name__ == "__main__":
    main()
