"""P5 RAG pipeline: P4 search -> Groq (cached) -> citation check.

Run from the repository root:  python -m eval.rag_pipeline
"""
from eval.citation_verifier import verify_citations
from src.common.config import ROOT, load_config
from src.rag.llm_cache import generate_cached
from src.search.search_service import search

SYSTEM_PROMPT_PATH = ROOT / "prompts" / "system_prompt.txt"


def rag_answer(question: str, date: str = None):
    print(f"\n❓ Question: {question}")

    try:
        # Top 5 articles from P4. date is not passed yet: P3's get_version is
        # still a stub, so dated search would fail.
        retrieved_articles = search(question, k=5)
    except Exception as e:
        print(f"⚠️ Error calling P4's search: {e}")
        return None

    if not retrieved_articles:
        print("❌ P4's search returned 0 articles.")
        return None

    print(f"📚 Retrieved {len(retrieved_articles)} articles from P4's engine.")

    context = ""
    for art in retrieved_articles:
        # P4 returns the article number in the "number" field (data contract).
        art_num = art.get("number", "Inconnu")
        text_id = art.get("text_id", "")
        context += f"--- Article {art_num} ({text_id}) ---\n{art.get('text', '')}\n\n"

    system_prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    final_prompt = f"CONTEXTE (Articles de loi) :\n{context}\n\nQUESTION :\n{question}"

    print("🤖 Calling Groq...")
    config = load_config()
    answer = generate_cached(final_prompt, system_instruction=system_prompt, config=config)

    print("\n=== ANSWER ===")
    print(answer)
    print("==============\n")

    print("🔍 Verifying citations...")
    is_valid = verify_citations(answer, retrieved_articles)
    if not is_valid:
        print("⚠️ Warning: This answer contains hallucinated citations!")

    return answer, retrieved_articles


if __name__ == "__main__":
    rag_answer("Un contrat de travail peut-il être oral ?")
