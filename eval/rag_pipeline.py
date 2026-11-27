"""P5 RAG pipeline: P4 search -> Groq (cached) -> citation check.

Run from the repository root:
    python -m eval.rag_pipeline                  # one demo question
    python -m eval.rag_pipeline --batch          # every question in eval/questions.csv
    python -m eval.rag_pipeline --batch --dry-run   # build prompts only, no API call
"""
import argparse
import hashlib

import pandas as pd

from eval.citation_verifier import extract_citations, verify_citations
from src.common.config import ROOT, load_config, resolve_path
from src.rag.llm_cache import generate_cached
from src.search.search_service import search

SYSTEM_PROMPT_PATH = ROOT / "prompts" / "system_prompt.txt"
QUESTIONS = ROOT / "eval" / "questions.csv"
OUTPUT = ROOT / "eval" / "rag_answers.csv"  # eval/results/ is git-ignored


def build_prompt(question: str, retrieved_articles: list) -> str:
    context = ""
    for art in retrieved_articles:
        # P4 returns the article number in the "number" field (data contract).
        art_num = art.get("number", "Inconnu")
        text_id = art.get("text_id", "")
        context += f"--- Article {art_num} ({text_id}) ---\n{art.get('text', '')}\n\n"
    return f"CONTEXTE (Articles de loi) :\n{context}\n\nQUESTION :\n{question}"


def rag_answer(question: str, date: str = None, config: dict = None, dry_run: bool = False) -> dict:
    """Search, ask the LLM with the retrieved articles only, verify citations."""
    print(f"\n❓ Question: {question}")
    # Undated by default. A dated search currently returns only P3-tracked articles.
    retrieved_articles = search(question, date=date, k=5)
    print(f"📚 Retrieved {len(retrieved_articles)} articles: {[a.get('number') for a in retrieved_articles]}")

    system_prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    final_prompt = build_prompt(question, retrieved_articles)
    result = {"retrieved": retrieved_articles, "prompt": final_prompt, "system_prompt": system_prompt}
    if dry_run or not retrieved_articles:
        return result

    config = config or load_config()
    answer = generate_cached(final_prompt, system_instruction=system_prompt, config=config)
    print("🔍 Verifying citations...")
    result.update(answer=answer, cited=extract_citations(answer),
                  citations_valid=verify_citations(answer, retrieved_articles))
    return result


def is_cached(model: str, system_prompt: str, prompt: str, config: dict) -> bool:
    """Same key as src/rag/llm_cache.py: sha256(model + system + prompt)."""
    full = system_prompt + "\n---USER---\n" + prompt
    key = hashlib.sha256(f"{model}::{full}".encode("utf-8")).hexdigest()
    cache_dir = resolve_path(config.get("paths", {}).get("cache", "cache/llm"))
    return (cache_dir / f"{key}.json").exists()


def main(dry_run: bool = False) -> None:
    config = load_config()
    model = config["llm"]["model"]
    questions = pd.read_csv(QUESTIONS, encoding="utf-8-sig").fillna("")
    rows, new_calls = [], 0
    for q in questions.to_dict("records"):
        res = rag_answer(str(q["question"]), config=config, dry_run=True)
        cached = is_cached(model, res["system_prompt"], res["prompt"], config)
        new_calls += not cached
        tokens = (len(res["system_prompt"]) + len(res["prompt"])) // 3
        print(f"   {q['question_id']}: ~{tokens} prompt tokens, {'cached' if cached else 'NEW call'}")
        if not dry_run:
            res = rag_answer(str(q["question"]), config=config)
        rows.append({
            "question_id": q["question_id"], "category": q["category"], "question": q["question"],
            "reference_articles": q["reference_articles"], "model": model,
            "retrieved_articles": ";".join(str(a.get("number")) for a in res["retrieved"]),
            "retrieval_method": res["retrieved"][0].get("method", "") if res["retrieved"] else "",
            "rag_answer": res.get("answer", ""),
            "cited_by_model": ";".join(res.get("cited", [])),
            "citations_valid": res.get("citations_valid", ""),
            "is_correct": "", "error_type": "", "notes": "",
        })
    print(f"\n{len(rows)} questions, {new_calls} new API call(s){' (dry run: none made)' if dry_run else ''}")
    if not dry_run:
        pd.DataFrame(rows).to_csv(OUTPUT, index=False, encoding="utf-8-sig")
        print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", action="store_true", help="run every question in eval/questions.csv")
    parser.add_argument("--dry-run", action="store_true", help="build prompts only, no API call")
    args = parser.parse_args()
    if args.batch:
        main(dry_run=args.dry_run)
    else:
        res = rag_answer("Un contrat de travail peut-il être oral ?", dry_run=args.dry_run)
        print(res.get("answer", "(dry run)"))
