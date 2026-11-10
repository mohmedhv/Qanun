"""Evaluate Gemini without retrieval, reusing cached answers."""
import pandas as pd
from src.common.config import ROOT, load_config
from src.rag.llm_cache import generate_cached

ERROR_TYPES = ("invented_article", "wrong_version", "foreign_law", "no_source", "wrong_calculation", "none")


def main() -> None:
    config = load_config()
    questions = pd.read_csv(ROOT / "eval/questions.csv").fillna("")
    results = []
    for row in questions.to_dict("records"):
        answer = generate_cached(str(row["question"]), config=config)
        # Students review and fill correct/error_type; no automatic legal grading.
        results.append({"question": row["question"], "answer": answer, "correct": "", "error_type": ""})
    destination = ROOT / "eval/results/baseline_llm_alone.csv"
    destination.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(results, columns=["question", "answer", "correct", "error_type"]).to_csv(destination, index=False)
    print(f"Wrote {destination}")


if __name__ == "__main__":
    main()

