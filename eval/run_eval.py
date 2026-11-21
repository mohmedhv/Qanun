"""Starter retrieval evaluation with TODO for the complete pipeline."""
from pathlib import Path
import pandas as pd
from src.search.bm25_baseline import search

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    questions = pd.read_csv(ROOT / "eval/questions.csv", encoding="utf-8-sig").fillna("")
    labeled = found = 0
    out_scope = questions[questions["category"] == "hors_perimetre"]
    refusals = 0
    for row in questions.to_dict("records"):
        results = search(str(row["question"]), k=5)  # TODO: pass a date once the CSV has one
        refs = {item.strip() for item in str(row["reference_articles"]).split(";") if item.strip()}
        if refs:
            labeled += 1
            found += any(hit["article_number"] in refs for hit in results)
        # TODO: run full pipeline and count actual out-of-scope refusals.
    print(f"correct article in top-5: {found}/{labeled} labeled questions")
    print(f"refusal rate on out-of-scope questions: {refusals}/{len(out_scope)} (TODO: full pipeline)")


if __name__ == "__main__":
    main()
