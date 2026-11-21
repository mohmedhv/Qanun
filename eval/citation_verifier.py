import re

def verify_citations(llm_answer: str, retrieved_articles: list) -> bool:
    """
    Checks if the LLM invented article numbers that were not in the retrieved list.
    """
    # 1. Extract BOTH formats:
    #    - "Article 8", "Art. 8", "Article 63"
    #    - "L1242-1", "L1242‑1", "R1234-5"
    matches = re.findall(r'(?:Article|Art\.?)\s*(\d+)', llm_answer, re.IGNORECASE)
    french_matches = re.findall(r'([LR]\d+[\-‑]\d+)', llm_answer, re.IGNORECASE)
    
    cited_clean = list(set(matches + french_matches))
            
    if not cited_clean:
        print("❌ Verification Failed: The LLM did not cite any articles.")
        return False
        
    # 2. Extract the numbers of the articles P4 actually provided
    valid_numbers = [str(art.get('article_number', '')) for art in retrieved_articles]
    
    # 3. Check if the LLM's citations are in the valid list
    hallucinated = []
    for num in cited_clean:
        if num not in valid_numbers:
            hallucinated.append(num)
            
    if hallucinated:
        print(f"🚨 HALLUCINATION DETECTED! The LLM cited articles that P4 did not provide: {hallucinated}")
        print(f"   Valid articles from P4: {valid_numbers}")
        return False
        
    print("✅ All citations are valid and exist in the retrieved context.")
    return True
