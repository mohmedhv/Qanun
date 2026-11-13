"""LLM-alone baseline (no retrieval) with the project LLM. Answers are cached."""
import pandas as pd

from src.common.config import ROOT, load_config
from src.rag.llm_cache import generate_cached


def main() -> None:
    config = load_config()
    questions = pd.read_csv(ROOT / "eval/questions.csv", encoding="utf-8-sig").fillna("")
    rows = []
    for q in questions.to_dict("records"):
        print(f"{q['question_id']} - {str(q['question'])[:60]}")
        answer = generate_cached(str(q["question"]), config=config)
        # Humans fill is_correct / error_type / cited_article / notes after reading the answer.
        rows.append({
            "question_id": q["question_id"], "category": q["category"],
            "question": q["question"], "reference_articles": q["reference_articles"],
            "llm_alone_answer": answer, "is_correct": "", "error_type": "",
            "cited_article": "", "notes": "",
        })
    destination = ROOT / "eval/baseline_llm_alone.csv"
    pd.DataFrame(rows).to_csv(destination, index=False, encoding="utf-8-sig")
    print(f"Wrote {destination}")


if __name__ == "__main__":
    main()
