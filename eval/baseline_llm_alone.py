"""LLM-alone baseline (no retrieval) with the project LLM. Answers are cached.

Each question is framed "En droit algérien, ..." so the model does not default
to French law. Run from the repo root:  python -m eval.baseline_llm_alone
"""
import pandas as pd

from src.common.config import ROOT, load_config
from src.rag.llm_cache import generate_cached

PREFIX = "En droit algérien, "


def frame(question: str, category: str = "") -> str:
    """Prefix the question with the jurisdiction, lowering its first letter.

    Out-of-scope questions (e.g. French law) are sent as written, so they
    still test whether the model answers outside the corpus.
    """
    question = question.strip()
    if category == "hors_perimetre":
        return question
    return PREFIX + question[:1].lower() + question[1:]


def main() -> None:
    config = load_config()
    model = config["llm"]["model"]
    questions = pd.read_csv(ROOT / "eval/questions.csv", encoding="utf-8-sig").fillna("")
    rows = []
    for q in questions.to_dict("records"):
        prompt = frame(str(q["question"]), str(q["category"]))
        print(f"{q['question_id']} - {prompt[:70]}")
        answer = generate_cached(prompt, config=config)
        # Humans fill is_correct / error_type / cited_article / notes after reading the answer.
        rows.append({
            "question_id": q["question_id"], "category": q["category"],
            "question": q["question"], "prompt_sent": prompt, "model": model,
            "reference_articles": q["reference_articles"],
            "llm_alone_answer": answer, "is_correct": "", "error_type": "",
            "cited_article": "", "notes": "",
        })
    destination = ROOT / "eval/baseline_llm_alone.csv"
    pd.DataFrame(rows).to_csv(destination, index=False, encoding="utf-8-sig")
    print(f"Wrote {destination}")


if __name__ == "__main__":
    main()
