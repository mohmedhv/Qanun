import sys
import os

from citation_verifier import verify_citations

# 1. Add root folder to path FIRST (before any src imports!)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 2. Now it's safe to import from src
from src.search.search_service import search
from src.rag.llm_cache import generate_cached
from src.common.config import load_config

def rag_answer(question: str, date: str = None):
    print(f"\n❓ Question: {question}")
    
    try:
        # We ask P4 for the top 5 articles. 
        # Note: we temporarily removed date=date because P3 is bypassed.
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
        art_num = art.get('article_number', 'Inconnu')
        text = art.get('text', '')
        context += f"--- Article {art_num} ---\n{text}\n\n"
        
    prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", "system_prompt.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        system_prompt = f.read()
        
    final_prompt = f"CONTEXTE (Articles de loi) :\n{context}\n\nQUESTION :\n{question}"
    
    print("🤖 Calling Groq...")
    config = load_config()
    answer = generate_cached(final_prompt, config=config)
    
    print("\n=== ANSWER ===")
    print(answer)
    print("==============\n")

    # 5. Verify citations (P5's job)
    print("🔍 Verifying citations...")
    is_valid = verify_citations(answer, retrieved_articles)
    if not is_valid:
        print("⚠️ Warning: This answer contains hallucinated citations!")
    
    return answer, retrieved_articles
    

if __name__ == "__main__":
    test_q = "Un contrat de travail peut-il être oral ?"
    rag_answer(test_q)